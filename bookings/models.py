from django.conf import settings
from django.db import models
from catalog.models import DiagnosticCentre, DiagnosticTest


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending payment"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FAILED = "FAILED", "Payment failed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bookings", on_delete=models.PROTECT)
    centre = models.ForeignKey(DiagnosticCentre, related_name="bookings", on_delete=models.PROTECT)
    diagnostic_test = models.ForeignKey(DiagnosticTest, related_name="bookings", on_delete=models.PROTECT)
    appointment_at = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "status"]), models.Index(fields=["appointment_at"])]

    def __str__(self):
        return f"Booking #{self.pk}: {self.status}"
