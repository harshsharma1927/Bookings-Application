from django.conf import settings
from django.db import models
from bookings.models import Booking


class Payment(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    booking = models.ForeignKey(Booking, related_name="payments", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=7, choices=Status.choices)
    idempotency_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    provider_event_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    source = models.CharField(max_length=16, default="api")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["booking", "status"])]


class WebhookEvent(models.Model):
    """Durable event ledger: a delivery is processed once even across worker restarts."""
    event_id = models.CharField(max_length=128, unique=True)
    payload = models.JSONField()
    processed_at = models.DateTimeField(auto_now_add=True)
