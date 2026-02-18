# app_club/forms.py

from django import forms
from .models import Actividad, Division, Rama,Entrenador, Ayudante, PF, Manager,StaffPermission,Presencialidad
from .models import Sede
from django.forms.widgets import CheckboxSelectMultiple, SelectDateWidget


class ActividadForm(forms.ModelForm):

    # 👇 SOLO PARA EL FORM (NO MODELO)
    SEDE_TIPO = [
        ("club", "Club Marista"),
        ("otro_club", "Otro club"),
        ("otro", "Otro lugar"),
    ]

    sede_tipo = forms.ChoiceField(
        choices=SEDE_TIPO,
        required=True,
        label="Tipo de sede"
    )

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.none(),
        required=True,
        label="Sede"
    )

    class Meta:
        model = Actividad
        fields = [
            "tipo",
            "fecha",
            "hora_inicio",   # 👈 NUEVO
            "hora_fin",      # 👈 NUEVO
            "division",
            "rama",
            "sede_tipo",     # 👈 NO está en el modelo
            "sede",          # 👈 SÍ está en el modelo
            "entrenadores",
            "ayudantes",
            "pfs",
            "managers",
        ]

        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),

            "entrenadores": CheckboxSelectMultiple(attrs={"class": "staff-checkbox"}),
            "ayudantes": CheckboxSelectMultiple(attrs={"class": "staff-checkbox"}),
            "pfs": CheckboxSelectMultiple(attrs={"class": "staff-checkbox"}),
            "managers": CheckboxSelectMultiple(attrs={"class": "staff-checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        # 1️⃣ PERMISOS (tal cual lo tenías)
        permisos = StaffPermission.objects.filter(user=user)

        divisiones_permitidas = permisos.values_list("division_id", flat=True)
        ramas_permitidas = permisos.values_list("rama_id", flat=True)

        self.fields["division"].queryset = Division.objects.filter(
            id__in=divisiones_permitidas
        )
        self.fields["rama"].queryset = Rama.objects.filter(
            id__in=ramas_permitidas
        )
        self.fields["rama"].widget.attrs.update({
            "onchange": "this.form.submit();"
        })

        # 2️⃣ DIVISIÓN / RAMA SELECCIONADA (tal cual)
        division = None
        rama = None

        if "division" in self.data and "rama" in self.data:
            try:
                division = Division.objects.get(id=self.data.get("division"))
                rama = Rama.objects.get(id=self.data.get("rama"))
            except:
                pass

        elif self.instance.pk:
            division = self.instance.division
            rama = self.instance.rama

        # 3️⃣ STAFF FILTRADO

        division = None
        rama = None

        if self.data.get("division"):
            try:
                division = int(self.data.get("division"))
            except (ValueError, TypeError):
                division = None

        if self.data.get("rama"):
            try:
                rama = int(self.data.get("rama"))
            except (ValueError, TypeError):
                rama = None

        if rama:
            self.fields["entrenadores"].queryset = Entrenador.objects.filter(
                ramas__id=rama
            ).distinct()

            self.fields["ayudantes"].queryset = Ayudante.objects.filter(
                ramas__id=rama
            ).distinct()

            self.fields["pfs"].queryset = PF.objects.filter(
                ramas__id=rama
            ).distinct()

            self.fields["managers"].queryset = Manager.objects.filter(
                ramas__id=rama
            ).distinct()
        else:
            self.fields["entrenadores"].queryset = Entrenador.objects.none()
            self.fields["ayudantes"].queryset = Ayudante.objects.none()
            self.fields["pfs"].queryset = PF.objects.none()
            self.fields["managers"].queryset = Manager.objects.none()

        # 4️⃣ 🔥 FILTRO DE SEDES SEGÚN sede_tipo (CLAVE)
        sede_tipo = None

        if "sede_tipo" in self.data:
            sede_tipo = self.data.get("sede_tipo")

        elif self.instance.pk and self.instance.sede:
            sede_tipo = self.instance.sede.tipo

        if sede_tipo:
            self.fields["sede"].queryset = Sede.objects.filter(tipo=sede_tipo)
        else:
            self.fields["sede"].queryset = Sede.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        entrenadores = cleaned_data.get("entrenadores")
        ayudantes = cleaned_data.get("ayudantes")
        pfs = cleaned_data.get("pfs")
        managers = cleaned_data.get("managers")

        if not entrenadores and not ayudantes and not pfs and not managers:
            raise forms.ValidationError(
                "Debés asignar al menos un integrante del staff "
                "(entrenador, ayudante, PF o manager)."
            )
        return cleaned_data        




class PresencialidadForm(forms.ModelForm):

    class Meta:
        model = Presencialidad
        fields = ["presente", "rendimiento"]

        widgets = {
            "presente": forms.CheckboxInput(attrs={"class": "check-presente"}),
            "rendimiento": forms.NumberInput(attrs={
                "min": 1,
                "max": 10,
                "style": "width:60px"
            }),
        }

    def save(self, commit=True, user=None):
        instancia = super().save(commit=False)

        # Auditoría
        if instancia.pk is None:
            instancia.creado_por = user
        else:
            instancia.modificado_por = user

        if commit:
            instancia.save()

        return instancia
    