# apps/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Cliente, Farmacia, Repartidor, ObraSocial

# --- 1. ADMIN DE USUARIO (Ya estaba bien) ---
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "email", 
        "first_name", 
        "last_name", 
        "is_staff", 
        "activo"
    )
    list_filter = (
        "is_staff", 
        "is_superuser", 
        "is_active", 
        "activo"
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "activo")}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(User, CustomUserAdmin)


# --- 2. ADMIN DE PERFILES (Aquí está la solución) ---

# Registro simple para Cliente y ObraSocial (no pediste filtros para estos)
admin.site.register(Cliente)
admin.site.register(ObraSocial)

# Decorador para registrar el modelo Farmacia con su clase Admin personalizada
@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista
    list_display = ('nombre', 'user', 'cuit', 'valido')
    
    # 💥 AÑADE EL FILTRO POR EL CAMPO 'valido' 💥
    list_filter = ('valido',)
    
    # (Opcional) Para poder buscar farmacias
    search_fields = ('nombre', 'cuit', 'user__email')
    
    # (Opcional) Para poder validar/invalidar desde la lista
    list_editable = ('valido',)

# Decorador para registrar el modelo Repartidor con su clase Admin personalizada
@admin.register(Repartidor)
class RepartidorAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista
    list_display = ('__str__', 'vehiculo', 'disponible', 'valido')
    
    # 💥 AÑADE EL FILTRO POR EL CAMPO 'valido' (y otros útiles) 💥
    list_filter = ('valido', 'disponible', 'vehiculo')
    
    # (Opcional) Para poder buscar repartidores
    search_fields = ('user__email', 'cuit', 'patente')
    
    # (Opcional) Para poder validar/invalidar y marcar disponible
    list_editable = ('disponible', 'valido')

