from django.contrib import admin
from .models import DiagnosticCentre, DiagnosticTest

admin.site.register(DiagnosticCentre)
admin.site.register(DiagnosticTest)
