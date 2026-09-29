from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from catalog.views import RegisterView
from rest_framework.schemas import get_schema_view
from rest_framework.permissions import AllowAny

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", TokenObtainPairView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/", include("catalog.urls")),
    path("api/", include("bookings.urls")),
    path("api/", include("payments.urls")),
    path("openapi/", get_schema_view(title="EVE Diagnostic Booking API", version="1.0.0", public=True,
         permission_classes=[AllowAny], authentication_classes=[]), name="openapi-schema"),
]
