from datetime import timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from bookings.models import Booking
from catalog.models import DiagnosticCentre, DiagnosticTest
from payments.models import Payment, WebhookEvent


class BookingPaymentAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="strong-password")
        self.other_user = User.objects.create_user(username="bob", email="bob@example.com", password="strong-password")
        self.centre = DiagnosticCentre.objects.create(name="Central Diagnostics", location="Bengaluru")
        self.test = DiagnosticTest.objects.create(centre=self.centre, name="CBC", price="500.00")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def create_booking(self):
        response = self.client.post("/api/bookings/", {
            "centre_id": self.centre.id, "diagnostic_test_id": self.test.id,
            "appointment_at": (timezone.now() + timedelta(days=1)).isoformat(),
        }, format="json")
        self.assertEqual(response.status_code, 201)
        return response.data["id"]

    def test_booking_snapshots_price_and_rejects_unavailable_test(self):
        booking_id = self.create_booking()
        booking = Booking.objects.get(pk=booking_id)
        self.assertEqual(str(booking.amount), "500.00")
        other = DiagnosticCentre.objects.create(name="Other", location="Mysuru")
        response = self.client.post("/api/bookings/", {
            "centre_id": other.id, "diagnostic_test_id": self.test.id,
            "appointment_at": (timezone.now() + timedelta(days=1)).isoformat(),
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_payment_idempotency_confirms_once(self):
        booking_id = self.create_booking()
        headers = {"HTTP_IDEMPOTENCY_KEY": "pay-001"}
        first = self.client.post("/api/payments/", {"booking_id": booking_id, "outcome": "SUCCESS"}, format="json", **headers)
        second = self.client.post("/api/payments/", {"booking_id": booking_id, "outcome": "SUCCESS"}, format="json", **headers)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Booking.objects.get(pk=booking_id).status, Booking.Status.CONFIRMED)

    def test_duplicate_webhook_has_no_duplicate_side_effect(self):
        booking_id = self.create_booking()
        body = {"event_id": "provider-event-123", "booking_id": booking_id, "status": "FAILED"}
        headers = {"HTTP_X_WEBHOOK_SECRET": "local-webhook-secret"}
        first = self.client.post("/api/payments/webhook/", body, format="json", **headers)
        repeated = self.client.post("/api/payments/webhook/", body, format="json", **headers)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(repeated.status_code, 200)
        self.assertTrue(repeated.data["duplicate"])
        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Booking.objects.get(pk=booking_id).status, Booking.Status.FAILED)

    def test_users_cannot_read_or_pay_for_another_users_booking(self):
        booking_id = self.create_booking()
        self.client.force_authenticate(self.other_user)
        response = self.client.post("/api/payments/", {"booking_id": booking_id, "outcome": "SUCCESS"}, format="json")
        self.assertEqual(response.status_code, 404)
