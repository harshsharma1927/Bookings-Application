from rest_framework import serializers
from .models import Payment


class PaymentRequestSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField(min_value=1)
    outcome = serializers.ChoiceField(choices=Payment.Status.choices)


class WebhookSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=128)
    booking_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=Payment.Status.choices)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "booking", "amount", "status", "source", "created_at")
        read_only_fields = fields
