from django.core.management.base import BaseCommand
from catalog.models import DiagnosticCentre, DiagnosticTest


CATALOGUE = [
    ("EVE Health - Indiranagar", "Indiranagar, Bengaluru", [
        ("Complete Blood Count", "Red blood cell, white blood cell and platelet analysis.", "450.00"),
        ("Thyroid Profile", "T3, T4 and TSH blood test.", "700.00"),
    ]),
    ("EVE Health - Koramangala", "Koramangala, Bengaluru", [
        ("HbA1c", "Average blood glucose over the previous 2-3 months.", "550.00"),
        ("Vitamin D", "25-hydroxy vitamin D blood test.", "900.00"),
    ]),
]


class Command(BaseCommand):
    help = "Create a small demonstration diagnostic catalogue. Safe to run repeatedly."

    def handle(self, *args, **options):
        for centre_name, location, tests in CATALOGUE:
            centre, _ = DiagnosticCentre.objects.get_or_create(name=centre_name, defaults={"location": location})
            for name, description, price in tests:
                DiagnosticTest.objects.update_or_create(
                    centre=centre, name=name, defaults={"description": description, "price": price, "is_active": True}
                )
        self.stdout.write(self.style.SUCCESS("Catalogue seeded."))
