from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for CustomUser.
    Adds the 'type' and profile fields to the admin interface.
    """
    model = CustomUser
    
    """ Display these fields in the user list """
    list_display = ['username', 'email', 'type', 'is_staff']
    
    """ Add custom fields to the Edit User page """
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('type', 'file', 'location', 'tel', 'description', 'working_hours')}),
    )
    
    """ Add custom fields to the Add User page """
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Info', {'fields': ('email', 'type')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)