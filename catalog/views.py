from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DiagnosticCentre
from .serializers import DiagnosticCentreSerializer, RegistrationSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]


class CentreListView(APIView):
    permission_classes = [permissions.AllowAny]
    cache_key = "catalogue:centres:v1"

    def get(self, request):
        payload = cache.get(self.cache_key)
        if payload is None:
            centres = DiagnosticCentre.objects.filter(is_active=True).prefetch_related("tests")
            payload = DiagnosticCentreSerializer(centres, many=True).data
            cache.set(self.cache_key, payload, timeout=300)
        return Response(payload, status=status.HTTP_200_OK)
