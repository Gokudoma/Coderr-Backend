from django.apps import AppConfig


class UserAuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_auth_app'
    verbose_name = 'User Management' # Better naming for Admin Panel