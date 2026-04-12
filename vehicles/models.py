from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Inspection(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='inspections/')
    result = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(default=0)