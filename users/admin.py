from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Columns shown in the user list
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')

    # Add the custom 'role' field into the existing fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

    def save_model(self, request, obj, form, change):
        # Keep is_staff / is_superuser in sync with role
        if obj.role == 'admin':
            obj.is_staff = True
            obj.is_superuser = True
        else:
            # Only strip flags if they weren't explicitly set via the
            # Permissions section in the form itself
            if 'is_staff' not in form.changed_data:
                obj.is_staff = False
            if 'is_superuser' not in form.changed_data:
                obj.is_superuser = False
        super().save_model(request, obj, form, change)