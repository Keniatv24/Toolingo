from django.contrib import admin
from .models import User
from .models import Profile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email","nombre","tipo_usuario")
    search_fields = ("email","nombre")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "nombre_completo", "pais", "ciudad", "status")
    list_filter = ("status", "pais", "ciudad")
    search_fields = ("user__email", "user__username", "nombre_completo", "numero_documento")
    readonly_fields = ("created_at", "updated_at", "terms_accepted_at")
