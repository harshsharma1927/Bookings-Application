from django.urls import path
from .views import BookingCancelView, BookingListCreateView

urlpatterns = [
    path("bookings/", BookingListCreateView.as_view(), name="booking-list-create"),
    path("bookings/<int:booking_id>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),
]
