# EVE diagnostic booking API

A Django REST Framework backend for booking diagnostic tests and processing simulated payments. It uses PostgreSQL for transactional data, Redis to cache the public catalogue, JWTs for client authentication, and a durable webhook-event ledger for idempotency.

## Run it

The fastest route is Docker (Docker Desktop required):

```bash
docker compose up --build
```

The API is then available at `http://localhost:8000`; development schema documentation is at `/openapi/`.

For a local Python run, first start PostgreSQL and Redis, then set the variables below (or copy `.env.example` to `.env` and export them in your shell):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_URL=postgresql://eve:eve@localhost:5432/eve
set REDIS_URL=redis://localhost:6379/1
set PAYMENT_WEBHOOK_SECRET=local-webhook-secret
python manage.py migrate
python manage.py seed_catalog
python manage.py runserver
```

`DATABASE_URL` is deliberately required in deployed environments. The SQLite fallback only supports quick local test execution when that variable is absent.

## API quick start

All request and response bodies are JSON. Authentication endpoints are public; all booking and direct payment endpoints require `Authorization: Bearer <access-token>`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Create a user (`username`, `email`, `password`) |
| `POST` | `/api/auth/login/` | Obtain JWT pair (`username`, `password`) |
| `POST` | `/api/auth/token/refresh/` | Refresh an access token |
| `GET` | `/api/centres/` | Cached public diagnostic-centre catalogue |
| `GET`, `POST` | `/api/bookings/` | List caller's bookings or create one |
| `POST` | `/api/bookings/{id}/cancel/` | Cancel a still-pending booking |
| `POST` | `/api/payments/` | Simulate a payment |
| `POST` | `/api/payments/webhook/` | Receive a provider payment event |

Create a booking:

```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"centre_id": 1, "diagnostic_test_id": 1, "appointment_at": "2027-01-15T09:30:00Z"}'
```

Simulate a successful payment. Supplying an `Idempotency-Key` makes safe client retries return the original payment rather than running the state change twice:

```bash
curl -X POST http://localhost:8000/api/payments/ \
  -H "Authorization: Bearer $TOKEN" -H "Idempotency-Key: checkout-42" -H "Content-Type: application/json" \
  -d '{"booking_id": 1, "outcome": "SUCCESS"}'
```

Send a webhook. In production the shared secret belongs in a secret manager and should be replaced with a provider signature scheme:

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "X-Webhook-Secret: local-webhook-secret" -H "Content-Type: application/json" \
  -d '{"event_id": "provider-event-42", "booking_id": 1, "status": "SUCCESS"}'
```

## Data design and decisions

`DiagnosticCentre` owns available `DiagnosticTest` rows. `Booking` references both and stores `amount` as a price snapshot, so a later catalogue price change cannot alter a booked amount. Booking states are `PENDING`, `CONFIRMED`, `FAILED`, and `CANCELLED`.

`Payment` is an immutable payment-attempt record. A direct call may carry a unique client idempotency key; provider callbacks use a unique `WebhookEvent.event_id` plus `Payment.provider_event_id`. Payment processing acquires a database row lock for the booking and updates its status in the same transaction as the payment record. Repeated webhook deliveries return `200` with `duplicate: true` without adding another payment or changing the booking.

The centre catalogue is cached in Redis for five minutes. The current catalogue is seeded with `python manage.py seed_catalog`; in a production admin workflow, invalidate the `catalogue:centres:v1` cache key when tests or centres change.

## Validation and security

- Only the booking owner can list, cancel, or directly pay for their booking.
- A test must belong to the requested active centre; appointments must be in the future.
- Only pending bookings can be paid or cancelled; terminal states cannot be overwritten.
- JWT protects customer operations. The webhook intentionally has no JWT but requires `X-Webhook-Secret`.
- Debug defaults are for local development only; set a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, restrictive `DJANGO_ALLOWED_HOSTS`, and a private webhook secret in deployment.

## Tests

```bash
python manage.py test
```

The tests cover booking price snapshots and test-centre validation, direct-payment idempotency, duplicate webhook delivery, and cross-user access protection.

## If I had more time

I would add provider-signed webhook payloads with key rotation, asynchronous retries and a dead-letter queue, booking-slot capacity/availability, API rate limits, staff CRUD endpoints and audit trails, structured logs/metrics, a production health check, and a CI pipeline running PostgreSQL/Redis integration tests.
