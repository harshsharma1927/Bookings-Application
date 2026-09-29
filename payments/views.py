import hmac
import os
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from bookings.models import Booking
from .models import Payment, WebhookEvent
from .serializers import PaymentRequestSerializer, PaymentSerializer, WebhookSerializer
from .services import record_payment


class PaymentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key")
        if key and len(key) > 128:
            return Response({"detail": "Idempotency-Key must be at most 128 characters."}, status=status.HTTP_400_BAD_REQUEST)
        booking = get_object_or_404(Booking, pk=serializer.validated_data["booking_id"], patient=request.user)
        if key:
            existing = Payment.objects.filter(idempotency_key=key).first()
            if existing:
                if existing.booking_id != booking.id:
                    return Response({"detail": "Idempotency key belongs to another booking."}, status=status.HTTP_409_CONFLICT)
                return Response(PaymentSerializer(existing).data, status=status.HTTP_200_OK)
        try:
            payment = record_payment(booking_id=booking.id, payment_status=serializer.validated_data["outcome"], source="api", idempotency_key=key)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError:
            # A concurrent retry using the same idempotency key won the race.
            payment = Payment.objects.get(idempotency_key=key)
            return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        expected = os.getenv("PAYMENT_WEBHOOK_SECRET", "local-webhook-secret")
        supplied = request.headers.get("X-Webhook-Secret", "")
        if not hmac.compare_digest(supplied, expected):
            return Response({"detail": "Invalid webhook credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            with transaction.atomic():
                event, created = WebhookEvent.objects.get_or_create(event_id=data["event_id"], defaults={"payload": request.data})
                if not created:
                    payment = Payment.objects.filter(provider_event_id=data["event_id"]).first()
                    body = PaymentSerializer(payment).data if payment else {"event_id": event.event_id}
                    return Response({"processed": False, "duplicate": True, "payment": body}, status=status.HTTP_200_OK)
                payment = record_payment(booking_id=data["booking_id"], payment_status=data["status"], source="webhook", provider_event_id=data["event_id"])
        except Booking.DoesNotExist:
            return Response({"detail": "Booking does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError:
            # The unique event ledger makes concurrent duplicate deliveries safe.
            payment = Payment.objects.filter(provider_event_id=data["event_id"]).first()
            return Response({"processed": False, "duplicate": True, "payment": PaymentSerializer(payment).data if payment else None})
        return Response({"processed": True, "duplicate": False, "payment": PaymentSerializer(payment).data}, status=status.HTTP_201_CREATED)
