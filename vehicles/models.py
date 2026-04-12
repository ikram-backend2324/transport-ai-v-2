from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Транспорт'
        verbose_name_plural = 'Транспорт'


class Inspection(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to='inspections/')
    result = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(default=0)

    def __str__(self):
        return f"{self.vehicle.name} — {self.user}"

    class Meta:
        verbose_name = 'Инспекция'
        verbose_name_plural = 'Инспекции'
        ordering = ['-created_at']
