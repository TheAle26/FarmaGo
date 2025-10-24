from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Renombramos el original para no confundir
from .models import User, Cliente, Farmacia, Repartidor, ObraSocial


class CustomUserAdmin(BaseUserAdmin):
    # Campos que se mostrarán en la lista (QUITAMOS USERNAME)
    list_display = (
        "email", 
        "first_name", 
        "last_name", 
        "is_staff", 
        "activo"
    )
    # Filtros para la lista
    list_filter = (
        "is_staff", 
        "is_superuser", 
        "is_active", 
        "activo"
    )
    # Campos de búsqueda
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    # El campo 'fieldsets' define el formulario de EDICIÓN.
    # Quitamos 'username' y añadimos 'activo'
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
    
    # IMPORTANTE: add_fieldsets define el formulario de CREACIÓN.
    # Debes quitar la referencia a 'username' y asegurar que solo pida 'email', 
    # 'password', y 'password2' (si tienes 'password2' en tu add form)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'), # Asegúrate de que 'password2' esté disponible si lo usas.
        }),
    )
    
    # También debemos especificar los campos a mostrar/editar en el formulario de agregar/cambiar
    # para que no busque el 'username'
    filter_horizontal = ('groups', 'user_permissions',) # Necesario para la vista de permisos

# ----------------------------------------------
# 2. Registrar los modelos
# ----------------------------------------------

admin.site.register(User, CustomUserAdmin)
admin.site.register(Cliente)
admin.site.register(Farmacia)
admin.site.register(Repartidor)
admin.site.register(ObraSocial)