from django.urls import path
from . import views

app_name = "app_club"

urlpatterns = [
    
    #path("actividad/nueva/", views.cargaA, name="cargaA"),
    #path("actividad/<int:actividad_id>/entrenadores/", views.presencialidad_entrenadores, name="presencialidad_entrenadores"),
    #path("actividad/<int:actividad_id>/entrenador/<int:entrenador_id>/presente/", views.ajax_marcar_presencia_entrenador, name="ajax_marcar_presencia_entrenador"),
    #path("actividad/<int:actividad_id>/jugadoras/", views.presencialidad_jugadoras, name="presencialidad_jugadoras"),

    path('', views.root_redirect, name='root'),
    path('areas/', views.areas, name='areas'),
    path('nueva_actividad/', views.nueva_actividad, name='nueva_actividad'), #FUNCION DE CARGA ACTIVIDAD
    path("nueva_actividad/editar/<int:id>/",views.editar_actividad,name="editar_actividad"), #FUNCION DE EDITAR ACTIVIDAD
    path("cargar_presencialidad",views.cargar_presencialidad,name="cargar_presencialidad"), #FUNCION DE EDITAR ACTIVIDAD
    path('lista_actividades/', views.lista_actividades, name='lista_actividades'), #VISTA
    path("actividad/<int:id>/presencialidad-jugadoras/",views.carga_presencialidad_jugadora,
       name="presencialidad_jugadoras"), #FUNCION DE CARGA PRESENCIALIDAD JUGADORA
    path("actividad/<int:id>/presencialidad-entrenadores/",views.carga_presencialidad_entrenadores,
       name="presencialidad_entrenadores"), #FUNCION DE CARGA PRESENCIALIDAD ENTRENADORES
    path('reporte/asistencias/', views.reporte_asistencias, name="reporte_asistencias"),
    path('reporte/entrenadores/', views.reporte_entrenadores, name="reporte_entrenadores"),
    path("ajax/sedes/", views.ajax_sedes_por_tipo, name="ajax_sedes_por_tipo"),
    path('ajax/staff/', views.cargar_staff, name='cargar_staff'),
    path("ajax/jugadoras/", views.ajax_tabla_jugadoras, name="ajax_tabla_jugadoras"),
    path("reporte/actividades/", views.reporte_actividades, name="reporte_actividades"),

           
]