from django.contrib import admin
from .models import (
    Rama, Division, Jugadora, StaffPermission, Actividad,
    Entrenador, Ayudante, PF, Manager, Presencialidad, Sede
)
from import_export.admin import ImportExportModelAdmin
from .recursos import JugadoraResource, ActividadResource

# ------------------------------------------------
# Función helper para registrar modelos simples de forma segura
# ------------------------------------------------
def safe_register(model, admin_class=None):
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass


# ------------------------------------------------
# Admins con import-export
# ------------------------------------------------
@admin.register(Jugadora)
class JugadoraAdmin(ImportExportModelAdmin):
    resource_class = JugadoraResource
    list_display = ('nombre', 'nro_socio', 'anio_nacimiento', 'division', 'rama')
    list_filter = ('division', 'rama')
    search_fields = ('nombre',)


@admin.register(Actividad)
class ActividadAdmin(ImportExportModelAdmin):
    resource_class = ActividadResource
    list_display = ('tipo', 'fecha', 'hora_inicio', 'hora_fin', 'division', 'rama', 'sede')
    list_filter = ('tipo', 'division', 'rama', 'sede')
    search_fields = ('tipo',)


# ------------------------------------------------
# Admins normales
# ------------------------------------------------
@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "lat", "long")
    list_filter = ("tipo",)
    search_fields = ("nombre",)


# ------------------------------------------------
# Registro seguro de modelos simples
# ------------------------------------------------
safe_register(Rama)
safe_register(Division)
safe_register(Entrenador)
safe_register(Ayudante)
safe_register(PF)
safe_register(Manager)
safe_register(StaffPermission)
safe_register(Presencialidad)








