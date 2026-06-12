from django.contrib import admin
from .models import Vehicle, Inspection


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('vehicle_display', 'user', 'mode', 'confidence', 'created_at')
    list_filter = ('mode', 'vehicle', 'user')
    search_fields = ('vehicle__name', 'custom_vehicle', 'user__username',
                     'brand', 'model_name')
    readonly_fields = ('result', 'metrics_json', 'confidence',
                       'created_at', 'image')
    ordering = ('-created_at',)

    def vehicle_display(self, obj):
        return obj.vehicle_display
    vehicle_display.short_description = 'Vehicle'
