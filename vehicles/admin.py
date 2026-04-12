from django.contrib import admin
from .models import Vehicle, Inspection


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'user', 'confidence', 'created_at')
    list_filter = ('vehicle', 'user')
    search_fields = ('vehicle__name', 'user__username')
    readonly_fields = ('result', 'confidence', 'created_at', 'image')
    ordering = ('-created_at',)
