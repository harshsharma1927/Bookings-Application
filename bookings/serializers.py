from django.utils import timezone
from rest_framework import serializers
from catalog.models import DiagnosticTest
from .models import Booking


class BookingCreateSerializer(serializers.ModelSerializer):
    centre_id = serializers.IntegerField(write_only=True)
    diagnostic_test_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = ("id", "centre_id", "diagnostic_test_id", "appointment_at", "amount", "status")
        read_only_fields = ("id", "amount", "status")

    def validate_appointment_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment must be in the future.")
        return value

    def validate(self, attrs):
        try:
            diagnostic_test = DiagnosticTest.objects.select_related("centre").get(
                pk=attrs["diagnostic_test_id"], centre_id=attrs["centre_id"], is_active=True, centre__is_active=True
            )
        except DiagnosticTest.DoesNotExist:
            raise serializers.ValidationError({"diagnostic_test_id": "Test is not available at this centre."})
        attrs["diagnostic_test"] = diagnostic_test
        attrs["centre"] = diagnostic_test.centre
        return attrs

    def create(self, validated_data):
        validated_data.pop("centre_id")
        validated_data.pop("diagnostic_test_id")
        test = validated_data.pop("diagnostic_test")
        centre = validated_data.pop("centre")
        return Booking.objects.create(
            patient=self.context["request"].user, centre=centre, diagnostic_test=test,
            amount=test.price, **validated_data
        )


class BookingSerializer(serializers.ModelSerializer):
    centre_name = serializers.CharField(source="centre.name", read_only=True)
    test_name = serializers.CharField(source="diagnostic_test.name", read_only=True)

    class Meta:
        model = Booking
        fields = ("id", "centre", "centre_name", "diagnostic_test", "test_name", "appointment_at", "amount", "status", "created_at")
        read_only_fields = fields
