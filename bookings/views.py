from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer


class BookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(patient=self.request.user).select_related("centre", "diagnostic_test")

    def get_serializer_class(self):
        # Schema generation instantiates the view without an HTTP request.
        if self.request is None or self.request.method == "POST":
            return BookingCreateSerializer
        return BookingSerializer


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, pk=booking_id, patient=request.user)
        if booking.status != Booking.Status.PENDING:
            return Response({"detail": "Only pending bookings may be cancelled."}, status=status.HTTP_409_CONFLICT)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        return Response(BookingSerializer(booking).data)
