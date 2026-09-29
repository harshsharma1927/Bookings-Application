from django.urls import path
from .views import PaymentCreateView, PaymentWebhookView

urlpatterns = [
    path("payments/", PaymentCreateView.as_view(), name="payment-create"),
    path("payments/webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
]
