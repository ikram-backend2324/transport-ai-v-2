from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    """Admin-added vehicle suggestions that users can pick from a dropdown."""
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Транспорт'
        verbose_name_plural = 'Транспорт'


class Inspection(models.Model):
    MODE_CHOICES = (
        ('simple', 'Simple'),
        ('detailed', 'Detailed'),
    )

    # Vehicle: either a picked Vehicle or a custom typed string
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True
    )
    custom_vehicle = models.CharField(max_length=200, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    image = models.ImageField(upload_to='inspections/')
    mode = models.CharField(
        max_length=10, choices=MODE_CHOICES, default='simple'
    )

    # Detailed mode optional fields
    brand = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    year = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=50, blank=True)
    mileage = models.CharField(max_length=50, blank=True)
    fuel_type = models.CharField(max_length=50, blank=True)
    transmission = models.CharField(max_length=50, blank=True)
    additional_info = models.TextField(blank=True)

    # AI output
    result = models.TextField(blank=True)
    metrics_json = models.TextField(blank=True)  # parsed structured metrics
    confidence = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_display} — {self.user}"

    @property
    def vehicle_display(self):
        if self.custom_vehicle:
            return self.custom_vehicle
        if self.vehicle:
            return self.vehicle.name
        return '—'

    class Meta:
        verbose_name = 'Инспекция'
        verbose_name_plural = 'Инспекции'
        ordering = ['-created_at']
