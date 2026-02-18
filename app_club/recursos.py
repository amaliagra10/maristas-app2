# app_club/resources.py
from import_export import resources, fields
from .models import Jugadora, Actividad, Division, Rama, Sede, Entrenador, Ayudante, PF, Manager
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget


class JugadoraResource(resources.ModelResource):
    division = fields.Field(
        column_name='division',
        attribute='division',
        widget=ForeignKeyWidget(Division, 'nombre')
    )
    rama = fields.Field(
        column_name='rama',
        attribute='rama',
        widget=ForeignKeyWidget(Rama, 'nombre')
    )

    class Meta:
        model = Jugadora
        fields = ('id', 'nombre', 'nro_socio', 'anio_nacimiento', 'division', 'rama')
        export_order = ('id', 'nombre', 'nro_socio', 'anio_nacimiento', 'division', 'rama')
 

class ActividadResource(resources.ModelResource):

    division = fields.Field(
        column_name='division',
        attribute='division',
        widget=ForeignKeyWidget(Division, 'nombre')
    )

    rama = fields.Field(
        column_name='rama',
        attribute='rama',
        widget=ForeignKeyWidget(Rama, 'nombre')
    )

    sede = fields.Field(
        column_name='sede',
        attribute='sede',
        widget=ForeignKeyWidget(Sede, 'nombre')
    )

    entrenadores = fields.Field(
        column_name='entrenadores',
        attribute='entrenadores',
        widget=ManyToManyWidget(Entrenador, field='nombre', separator=';')
    )

    ayudantes = fields.Field(
        column_name='ayudantes',
        attribute='ayudantes',
        widget=ManyToManyWidget(Ayudante, field='nombre', separator=';')
    )

    pfs = fields.Field(
        column_name='pfs',
        attribute='pfs',
        widget=ManyToManyWidget(PF, field='nombre', separator=';')
    )

    managers = fields.Field(
        column_name='managers',
        attribute='managers',
        widget=ManyToManyWidget(Manager, field='nombre', separator=';')
    )

    class Meta:
        model = Actividad
        fields = (
            'id', 'tipo', 'fecha', 'hora_inicio', 'hora_fin',
            'division', 'rama', 'sede',
            'entrenadores', 'ayudantes', 'pfs', 'managers'
        )
