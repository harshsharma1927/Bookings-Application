from django.db import models


class DiagnosticCentre(models.Model):
    name = models.CharField(max_length=160)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.location})"


class DiagnosticTest(models.Model):
    centre = models.ForeignKey(DiagnosticCentre, related_name="tests", on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["centre", "name"], name="unique_test_per_centre")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} at {self.centre.name}"
