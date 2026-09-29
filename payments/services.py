from django.db import transaction
from bookings.models import Booking
from .models import Payment


def record_payment(*, booking_id, payment_status, source, idempotency_key=None, provider_event_id=None):
    """Atomically write payment and move a pending booking to its terminal state."""
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(pk=booking_id)
        if booking.status != Booking.Status.PENDING:
            raise ValueError("Booking is no longer awaiting payment.")
        payment = Payment.objects.create(
            booking=booking, amount=booking.amount, status=payment_status, source=source,
            idempotency_key=idempotency_key, provider_event_id=provider_event_id,
        )
        booking.status = Booking.Status.CONFIRMED if payment_status == Payment.Status.SUCCESS else Booking.Status.FAILED
        booking.save(update_fields=["status", "updated_at"])
        return payment
