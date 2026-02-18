from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone



#   ------ ESTRUCTURA DEL CLUB-------------

class Division(models.Model):
    nombre = models.CharField(max_length=20)   # Ej: "6ta", "5ta", "7ma"
    def __str__(self):
        return self.nombre


class Rama(models.Model):
    nombre = models.CharField(max_length=10)   # "A", "B", "C"
    division = models.ForeignKey(Division, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.division.nombre} {self.nombre}"


# ---------- JUGADORAS---------------

class Jugadora(models.Model):
    nombre = models.CharField(max_length=100)
    nro_socio = models.CharField(max_length=20, blank=True, null=True)
    anio_nacimiento = models.IntegerField()
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    rama = models.ForeignKey(Rama, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.nombre

# ------- ENTRENADORES Y STAFF------------


class Entrenador(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=150,blank=True, null=True)

    divisiones = models.ManyToManyField(Division)
    ramas = models.ManyToManyField(Rama)

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Sin usuario"


class Ayudante(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=150,blank=True, null=True)

    divisiones = models.ManyToManyField(Division)
    ramas = models.ManyToManyField(Rama)

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Sin usuario"
    
class PF(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=150,blank=True, null=True)

    divisiones = models.ManyToManyField(Division)
    ramas = models.ManyToManyField(Rama)

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Sin usuario"
    
class Manager(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=150,blank=True, null=True)

    divisiones = models.ManyToManyField(Division)
    ramas = models.ManyToManyField(Rama)

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Sin usuario"
    
# -------------SEDE-----------------------
class Sede(models.Model):
    TIPO = [
        ("club", "Club Marista"),
        ("otro_club", "Otro club"),
        ("otro", "Otro lugar"),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO)
    lat= models.DecimalField(max_digits=9, decimal_places=6)
    long = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.nombre

# --------ACTIVIDADES-----------------------
class Actividad(models.Model):
    TIPO = [
        ('Técnico', 'Técnico'),
        ('Físico', 'Físico'),
        ('Partido', 'Partido'),
        ('Otra', 'Otra'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO)
    fecha = models.DateField()

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    rama = models.ForeignKey(Rama, on_delete=models.CASCADE)

    # ✅ ESTO ES LO CORRECTO
    sede = models.ForeignKey(
        Sede,
        on_delete=models.PROTECT,
        related_name="actividades",
        null=True,      # 👈 CLAVE
        blank=True
    )

    entrenadores = models.ManyToManyField(Entrenador, blank=True)
    ayudantes = models.ManyToManyField(Ayudante, blank=True)
    pfs = models.ManyToManyField(PF, blank=True)
    managers = models.ManyToManyField(Manager, blank=True)

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="actividades_creadas")
    creado_el = models.DateTimeField(default=timezone.now)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="actividades_modificadas")
    modificado_el = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.fecha} - {self.division} - {self.rama}"


#-----------PRESENCIALIDAD / RENDIMIENTO

class Presencialidad(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    jugadora = models.ForeignKey(Jugadora, on_delete=models.CASCADE)
    presente = models.BooleanField(default=False)
    rendimiento = models.IntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rendimiento del 1 al 10"
    )
    # Auditoría
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,
        null=True, blank=True,related_name='presenc_creada')
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,
        null=True, blank=True,related_name='presenc_modificada')
    eliminado_por = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,
        null=True, blank=True,related_name='presenc_eliminada')
    creado_el = models.DateTimeField(auto_now_add=True)
    modificado_el = models.DateTimeField(auto_now=True)
    eliminado_el = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('actividad', 'jugadora')
        verbose_name = "Presencialidad"
        verbose_name_plural = "Presencialidades"
    def __str__(self):
        return f"{self.jugadora} - {self.actividad}"
    

class PresencialidadEntrenador(models.Model):
    actividad = models.ForeignKey(Actividad,on_delete=models.CASCADE,
        related_name="presencias_entrenadores")
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="presencias_en_actividades"
    )
    presente = models.BooleanField(default=False)

       # ✅ Campos nuevos
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("actividad", "usuario")

    def __str__(self):
        return f"{self.usuario} – {self.actividad}"



#-----------PERMISOS-----------------------------    

class StaffPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    rama = models.ForeignKey(Rama, on_delete=models.CASCADE)
    tipo = models.CharField(
        max_length=20,
        choices=Actividad.TIPO,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} puede cargar {self.division} {self.rama} {self.tipo}"
