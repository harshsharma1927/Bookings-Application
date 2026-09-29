from django.contrib.auth.models import User
from rest_framework import serializers
from .models import DiagnosticCentre, DiagnosticTest


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"email": {"required": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class DiagnosticTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTest
        fields = ("id", "name", "description", "price")


class DiagnosticCentreSerializer(serializers.ModelSerializer):
    tests = DiagnosticTestSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticCentre
        fields = ("id", "name", "location", "tests")
