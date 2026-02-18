from django.shortcuts import render, redirect, get_object_or_404
from .models import Presencialidad,Jugadora,Division
from .forms import ActividadForm, PresencialidadForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Rama, Entrenador, Ayudante, PF, Manager
from django.http import JsonResponse
from .models import Entrenador, Ayudante, PF, Manager, Division, Rama,Actividad,StaffPermission,User
from .models import Sede, PresencialidadEntrenador
from django.contrib import messages
from django.db.models import Avg
from django.db.models import Q
from django.contrib import messages as dj_messages

#------------LOGIN---------------

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("app_club:areas")
    return redirect("login") 

#-----------AREAS-----------------
@login_required
def areas(request):
    return render(request, 'app_club/areas.html', {'user': request.user})


#----------ACTIVIDAD BASE------------------------
@login_required
def actividad_base(request,*,template,show_form=True,return_ctx=False):
    form = None
    actividad = None
    no_guardado = False
    # 1) ALTA DE ACTIVIDAD
    if show_form:
        if request.method == "POST":
            form = ActividadForm(request.POST, user=request.user)

            if form.is_valid():
                actividad = form.save(commit=False)
                actividad.creado_por = request.user
                actividad.save()
                form.save_m2m()

                return redirect("app_club:lista_actividades")
            else:
                no_guardado = True
                dj_messages.error(
                    request,
                    "No se pudo guardar la actividad. Revisá los campos."
                )

        else:
            # GET → defaults
            initial = {"sede_tipo": "club"}
            form = ActividadForm(user=request.user, initial=initial)

            sedes_club = Sede.objects.filter(tipo="club")
            form.fields["sede"].queryset = sedes_club

            try:
                sede_default = sedes_club.get(nombre__iexact="Club Marista")
                form.fields["sede"].initial = sede_default.id
            except Sede.DoesNotExist:
                pass

    # 2) QUERY BASE ACTIVIDADES
    actividades = (
        Actividad.objects
        .select_related("division", "rama", "sede")
        .prefetch_related(
            "entrenadores",
            "ayudantes",
            "pfs",
            "managers"
        )
    )

    # 3) FILTRO POR USUARIO
    permisos = StaffPermission.objects.filter(user=request.user)
    divisiones = permisos.values_list("division_id", flat=True)
    ramas = permisos.values_list("rama_id", flat=True)

    actividades = actividades.filter(
        Q(creado_por=request.user) |
        Q(division_id__in=divisiones, rama_id__in=ramas)
    ).distinct()

    # 4) CONTEXTO
    ctx = {
        "form": form,
        "actividad": actividad,
        "actividades": actividades,
        "no_guardado": no_guardado,
    }

    if return_ctx:
        return ctx

    return render(request, template, ctx)


#-------------CARGA Y EDICION----------------------    
@login_required
def nueva_actividad(request):
    return actividad_base(
        request,
        template="app_club/nueva_actividad.html",
        show_form=True
    )


@login_required
def carga_presencialidad_jugadora(request, id):
    actividad = get_object_or_404(Actividad, pk=id)

    jugadoras = Jugadora.objects.filter(
        division=actividad.division,
        rama=actividad.rama
    )

    if request.method == "POST":
        for j in jugadoras:
            pres, _ = Presencialidad.objects.get_or_create(
                actividad=actividad,
                jugadora=j
            )

            pres.presente = f"presente_{j.id}" in request.POST

            valor = request.POST.get(f"rendimiento_{j.id}")
            if valor and valor.isdigit():
                pres.rendimiento = int(valor)

            pres.save()

        messages.success(
            request,
            "Presencialidad de jugadoras guardada correctamente."
        )

        return redirect("app_club:lista_actividades")

    # 👇 GET → muestra la pantalla
    return render(
        request,
        "app_club/presencialidad_jugadoras.html",
        {
            "actividad": actividad,
            "jugadoras": jugadoras,
        }
    )

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden

from .models import Actividad, PresencialidadEntrenador
from .auxiliar import distancia_metros, get_client_ip


@login_required
def carga_presencialidad_entrenadores(request, id):
    actividad = get_object_or_404(Actividad, pk=id)
    user = request.user
    autorizado = False

    # 🔹 Verificamos rol del usuario
    if hasattr(user, "entrenador") and actividad.entrenadores.filter(id=user.entrenador.id).exists():
        autorizado = True
    if hasattr(user, "ayudante") and actividad.ayudantes.filter(id=user.ayudante.id).exists():
        autorizado = True
    if hasattr(user, "pf") and actividad.pfs.filter(id=user.pf.id).exists():
        autorizado = True

    if not autorizado:
        return HttpResponseForbidden("No estás asignado a esta actividad.")
    
    """# Validar fecha y horario
    now = timezone.localtime()

    fecha_actividad = actividad.fecha
    hora_inicio = actividad.hora_inicio
    hora_fin = actividad.hora_fin

    # Verificar que sea el mismo día
    if now.date() != fecha_actividad:
        return JsonResponse(
            {"error": "Solo podés marcar presencialidad el día de la actividad"},
            status=400
        )

    # Verificar que esté dentro del rango horario
    if not (hora_inicio <= now.time() <= hora_fin):
        return JsonResponse(
            {"error": "Estás fuera del horario permitido para marcar presencialidad"},
            status=400
        )"""

    pres, _ = PresencialidadEntrenador.objects.get_or_create(
        actividad=actividad,
        usuario=user
    )

    if request.method == "POST":

        lat = request.POST.get("lat")
        lon = request.POST.get("lon")
        ip = get_client_ip(request)

        if pres.presente:
            return JsonResponse(
                {"error": "Ya marcaste tu presencialidad para esta actividad"},
                status=400
            )

        # Validar coordenadas
        if not lat or not lon:
            return JsonResponse({"error": "Faltan coordenadas"}, status=400)

        if not actividad.sede:
            return JsonResponse({"error": "La actividad no tiene sede configurada"}, status=400)

        # Calcular distancia
        distancia = distancia_metros(
            float(lat),
            float(lon),
            actividad.sede.lat,
            actividad.sede.long
        )

        RADIO_PERMITIDO = 1500  # metros

        if distancia > RADIO_PERMITIDO:
            return JsonResponse({
                "error": f"No estás dentro del área permitida ({int(distancia)} m)"
            }, status=400)

        # 🔹 Guardamos presencialidad
        pres.presente = True
        pres.lat = float(lat)
        pres.lon = float(lon)
        pres.ip = ip
        pres.save()

        return JsonResponse({"success": "Presencialidad registrada"})

    return render(
        request,
        "app_club/presencialidad_entrenadores.html",
        {"actividad": actividad, "presencia": pres}
    )


@login_required
def editar_actividad(request, id):
    actividad = get_object_or_404(Actividad, id=id)

    form = ActividadForm(request.POST or None,instance=actividad,user=request.user)

    if request.method == "POST":
        if form.is_valid():
            obj = form.save(commit=False)
            obj.modificado_por = request.user
            obj.save()
            form.save_m2m()

            dj_messages.success(request,
                "Actividad modificada correctamente.")

            return redirect("app_club:lista_actividades")
        else:
            dj_messages.error(
                request,
                "No se pudo actualizar la actividad. Revisá los campos."
            )

    return render(
        request,
        "app_club/nueva_actividad.html",
        {
            "form": form,
            "actividad": actividad,
            "editing": True,   # 👈 útil si después querés cambiar títulos/botones
        }
    )



#----------------- TABLA-----------------------

from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

@login_required
def cargar_presencialidad(request):

    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)

    # 🔹 permisos
    permisos = StaffPermission.objects.filter(user=request.user)
    divisiones = permisos.values_list("division_id", flat=True)
    ramas_ids = permisos.values_list("rama_id", flat=True)

   
    if divisiones or ramas_ids:
        qs = Actividad.objects.filter(
            Q(creado_por=request.user) |
            Q(division_id__in=divisiones, rama_id__in=ramas_ids)
        ).distinct()
    else:
        # si no tiene permisos cargados, solo lo creado por él
        qs = Actividad.objects.filter(creado_por=request.user)

    qs = qs.filter(
        Q(fecha=hoy) |
        Q(fecha=ayer, hora_fin__gt="22:00")     
    )
   
    ctx = {
    "actividades": qs,
    "ramas": Rama.objects.all(),
    "tipos": Actividad.TIPO,
}


    # 🔎 filtros manuales
    rama = request.GET.get("rama")
    tipo = request.GET.get("tipo")

    if rama:
        qs = qs.filter(rama_id=rama)

    if tipo:
        qs = qs.filter(tipo=tipo)

    ctx = {
        "actividades": qs.order_by("fecha", "hora_inicio"),
        "ramas": Rama.objects.filter(id__in=ramas_ids),
        "tipos": Actividad.TIPO,
    }

    return render(request, "app_club/cargar_presencialidad.html", ctx)




@login_required
def lista_actividades(request):
    

    ctx = actividad_base(
        request,
        template="app_club/lista_actividades.html",
        show_form=False,
        return_ctx=True
    )

    permisos = StaffPermission.objects.filter(user=request.user)
    ramas_permitidas = permisos.values_list("rama_id", flat=True)
    ctx["ramas"] = Rama.objects.filter(id__in=ramas_permitidas)
    ctx["tipos"] = Actividad.TIPO

    qs = ctx["actividades"]

    # 🔎 FILTROS
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    rama = request.GET.get("rama")
    tipo = request.GET.get("tipo")

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    if rama:
        qs = qs.filter(rama_id=rama)

    if tipo:
        qs = qs.filter(tipo=tipo)

    ctx["actividades"] = qs.order_by("fecha", "creado_el", "id")

    return render(request, "app_club/lista_actividades.html", ctx)


#1 Asistencia y Rendimiento
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.shortcuts import render

@login_required
def reporte_asistencias(request):

    # ───────── PERMISOS ─────────
    permisos = StaffPermission.objects.filter(user=request.user)
    divisiones_permitidas = permisos.values_list("division_id", flat=True)
    ramas_permitidas = permisos.values_list("rama_id", flat=True)

    # ───────── FILTROS ─────────
    division_id = request.GET.get("division")
    rama_id = request.GET.get("rama")
    fecha_desde = request.GET.get("desde")
    fecha_hasta = request.GET.get("hasta")

    mostrar_tabla = bool(division_id and rama_id)

    # ───────── ACTIVIDADES (solo visual) ─────────
    actividades = Actividad.objects.filter(
        division_id__in=divisiones_permitidas,
        rama_id__in=ramas_permitidas
    )

    if division_id:
        actividades = actividades.filter(division_id=division_id)

    if rama_id:
        actividades = actividades.filter(rama_id=rama_id)

    if fecha_desde:
        actividades = actividades.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        actividades = actividades.filter(fecha__lte=fecha_hasta)

    actividades = actividades.order_by("-fecha")

    divisiones = Division.objects.filter(id__in=divisiones_permitidas)
    ramas = Rama.objects.filter(id__in=ramas_permitidas)

    # ───────── PRESENCIALIDADES BASE ─────────
    presencialidades = Presencialidad.objects.filter(
        actividad__division__in=divisiones_permitidas,
        actividad__rama__in=ramas_permitidas
    )

    if division_id:
        presencialidades = presencialidades.filter(
            actividad__division_id=division_id
        )

    if rama_id:
        presencialidades = presencialidades.filter(
            actividad__rama_id=rama_id
        )

    if fecha_desde:
        presencialidades = presencialidades.filter(
            actividad__fecha__gte=fecha_desde
        )

    if fecha_hasta:
        presencialidades = presencialidades.filter(
            actividad__fecha__lte=fecha_hasta
        )

    # ───────── PRESENCIALIDAD GENERAL POR JUGADORA ─────────
    presencialidad_por_jugadora = (
        presencialidades
        .values("jugadora_id", "jugadora__nombre")
        .annotate(
            total=Count("id"),
            presentes=Count("id", filter=Q(presente=True)),
            rendimiento_promedio=Avg(
                "rendimiento",
                filter=Q(presente=True, rendimiento__isnull=False)
            )
        )
        .order_by("jugadora__nombre")
    )

    for j in presencialidad_por_jugadora:
        j["porcentaje_presencialidad"] = (
            (j["presentes"] / j["total"]) * 100 if j["total"] > 0 else 0
        )

    # ───────── PRESENCIALIDAD POR JUGADORA Y TIPO ─────────
    presencialidad_por_jugadora_tipo = (
        presencialidades
        .values("jugadora_id", "actividad__tipo")
        .annotate(
            total=Count("id"),
            presentes=Count("id", filter=Q(presente=True)),
            rendimiento_promedio=Avg(
                "rendimiento",
                filter=Q(presente=True, rendimiento__isnull=False)
            )
        )
    )

    for r in presencialidad_por_jugadora_tipo:
        r["porcentaje_presencialidad"] = (
            (r["presentes"] / r["total"]) * 100 if r["total"] > 0 else 0
        )

    # ───────── ARMAR DATA PARA TEMPLATE ─────────
    data = []

    # indexar por (jugadora_id, tipo)
    por_tipo = {}
    for r in presencialidad_por_jugadora_tipo:
        tipo = r["actividad__tipo"].lower()
        por_tipo[(r["jugadora_id"], tipo)] = r

    for j in presencialidad_por_jugadora:
        jugadora_id = j["jugadora_id"]

        fila = {
            "jugadora": j["jugadora__nombre"],
            "pct_general": round(j["porcentaje_presencialidad"], 1),
            "rend_general": (
                round(j["rendimiento_promedio"], 1)
                if j["rendimiento_promedio"] is not None else "-"
            ),
            "tipos": {
                "técnico": {"pct": "-", "rend": "-"},
                "físico": {"pct": "-", "rend": "-"},
                "partido": {"pct": "-", "rend": "-"},
            }
        }

        for tipo in ["técnico", "físico" "partido"]:
            key = (jugadora_id, tipo)
            if key in por_tipo:
                fila["tipos"][tipo]["pct"] = round(
                    por_tipo[key]["porcentaje_presencialidad"], 1
                )
                fila["tipos"][tipo]["rend"] = (
                    round(por_tipo[key]["rendimiento_promedio"], 1)
                    if por_tipo[key]["rendimiento_promedio"] is not None else "-"
                )

        data.append(fila)

    # ───────── RENDER ─────────
    return render(request, "app_club/reporte_asistencias.html", {
        "actividades": actividades,
        "divisiones": divisiones,
        "ramas": ramas,
        "division_seleccionada": division_id,
        "rama_seleccionada": rama_id,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "mostrar_tabla": mostrar_tabla,
        "data": data,
    })

@login_required
def reporte_entrenadores(request):

    # ───────── PERMISOS ─────────
    permisos = StaffPermission.objects.filter(user=request.user)
    divisiones_permitidas = permisos.values_list("division_id", flat=True)
    ramas_permitidas = permisos.values_list("rama_id", flat=True)

    # ───────── FILTROS ─────────
    division_id = request.GET.get("division")
    rama_id = request.GET.get("rama")

    mostrar_tabla = True  # 👈 ahora SIEMPRE se muestra

    # ───────── SELECTORES ─────────
    divisiones = Division.objects.filter(id__in=divisiones_permitidas)
    ramas = Rama.objects.filter(id__in=ramas_permitidas)

    # ───────── ENTRENADORES (BASE) ─────────
    entrenadores = User.objects.filter(
        presencias_en_actividades__actividad__division__in=divisiones_permitidas
    ).distinct().order_by("last_name", "first_name")

    # ───────── PRESENCIALIDADES BASE (SIN FILTRO DE RAMA) ─────────
    presencias_base = PresencialidadEntrenador.objects.filter(
        actividad__division__in=divisiones_permitidas
    )

    # ───────── PRESENCIALIDADES FILTRADAS ─────────
    presencias_filtradas = presencias_base

    if division_id:
        presencias_filtradas = presencias_filtradas.filter(
            actividad__division_id=division_id
        )

    if rama_id:
        presencias_filtradas = presencias_filtradas.filter(
            actividad__rama_id=rama_id
        )

    data = []

    for user in entrenadores:

        # ───── GENERAL (sin filtro de rama) ─────
        qs_general = presencias_base.filter(usuario=user)

        total_general = qs_general.count()
        presentes_general = qs_general.filter(presente=True).count()

        pct_general = (
            (presentes_general / total_general) * 100
            if total_general > 0 else 0
        )

        fila = {
            "entrenador": user.get_full_name() or user.username,
            "pct_general": round(pct_general, 1),
            "total_general": total_general,
            "tipos": {
                "Técnico": {"pct": "-", "total": 0},
                "Físico": {"pct": "-", "total": 0},
                "Partido": {"pct": "-", "total": 0},
            }
        }

        # ───── POR TIPO (CON FILTROS) ─────
        for tipo in ["Técnico", "Físico", "Partido"]:
            qs_tipo = presencias_filtradas.filter(
                usuario=user,
                actividad__tipo=tipo
            )

            total = qs_tipo.count()
            presentes = qs_tipo.filter(presente=True).count()

            if total > 0:
                fila["tipos"][tipo]["pct"] = round(
                    (presentes / total) * 100, 1
                )
                fila["tipos"][tipo]["total"] = total

        data.append(fila)

    print(data)    

    # ───────── RENDER ─────────
    return render(request, "app_club/reporte_entrenadores.html", {
        "divisiones": divisiones,
        "ramas": ramas,
        "division_seleccionada": division_id,
        "rama_seleccionada": rama_id,
        "mostrar_tabla": mostrar_tabla,
        "data": data,
    })

#2 ACTIVIADES
@login_required
def reporte_actividades(request):

    permisos = StaffPermission.objects.filter(user=request.user)
    divisiones_permitidas = permisos.values_list("division_id", flat=True)
    ramas_permitidas = permisos.values_list("rama_id", flat=True)

    division_id = request.GET.get("division")
    rama_id = request.GET.get("rama")
    fecha_desde = request.GET.get("desde")
    fecha_hasta = request.GET.get("hasta")

    # Solo mostrar tabla si eligió ambas
    mostrar_tabla = (division_id and rama_id)

    actividades = Actividad.objects.filter(
        division_id__in=divisiones_permitidas,
        rama_id__in=ramas_permitidas
    )

    if division_id:
        actividades = actividades.filter(division_id=division_id)

    if rama_id:
        actividades = actividades.filter(rama_id=rama_id)

    # 🔹 FILTRO POR FECHA
    if fecha_desde:
        actividades = actividades.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        actividades = actividades.filter(fecha__lte=fecha_hasta)    

    actividades = actividades.order_by("-fecha")    

    divisiones = Division.objects.filter(id__in=divisiones_permitidas)
    ramas = Rama.objects.filter(id__in=ramas_permitidas)

    print("ACTIVIDADES ENCONTRADAS:", actividades.count())
    for a in actividades:
        print("→", a.id, a.fecha, a.tipo, a.entrenadores)

    return render(request, "app_club/reporte_actividades.html", {
        "actividades": actividades,
        "divisiones": divisiones,
        "ramas": ramas,
        "division_seleccionada": division_id,
        "rama_seleccionada": rama_id,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "mostrar_tabla": mostrar_tabla,
    })

#----------------- AJAX-----------------------

def cargar_staff(request):
    division_id = request.GET.get("division")
    rama_id = request.GET.get("rama")

    if not division_id or not rama_id:
        return JsonResponse({"ok": False, "msg": "faltan parámetros"})

    try:
        division = Division.objects.get(id=division_id)
        rama = Rama.objects.get(id=rama_id)
    except:
        return JsonResponse({"ok": False, "msg": "division o rama inválida"})

    # ---- FILTRAMOS POR DIVISION + RAMA ----
    entrenadores = Entrenador.objects.filter(divisiones=division, ramas=rama)\
                                     .values("id", "nombre")
    ayudantes = Ayudante.objects.filter(divisiones=division, ramas=rama)\
                                 .values("id", "nombre")
    pfs = PF.objects.filter(divisiones=division, ramas=rama)\
                     .values("id", "nombre")
    managers = Manager.objects.filter(divisiones=division, ramas=rama)\
                               .values("id", "nombre")

    return JsonResponse({
        "ok": True,
        "entrenadores": list(entrenadores),
        "ayudantes": list(ayudantes),
        "pfs": list(pfs),
        "managers": list(managers),
    })
@login_required
def ajax_tabla_jugadoras(request):
    division_id = request.GET.get("division")
    rama_id = request.GET.get("rama")

    if not division_id:
        return JsonResponse({"jugadoras": []})

    jugadoras = Jugadora.objects.filter(division=division_id)

    data = []
    for j in jugadoras:
        data.append({
            "id": j.id,
            "nombre": str(j),
        })

    return JsonResponse({"jugadoras": data}) 

@login_required
def ajax_sedes_por_tipo(request):
    tipo = request.GET.get("tipo")
    sedes = Sede.objects.filter(tipo=tipo).values("id", "nombre")
    return JsonResponse(list(sedes), safe=False)

#-----------------GEOLOCALIZACION-------------------------------------
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Sede, Actividad, PresencialidadEntrenador
from .serializers import PresencialidadEntrenadorSerializer
from .auxiliar import distancia_metros, get_client_ip

# ------------------------------------------------------------
# Vista para que el entrenador registre su propia presencialidad
# ------------------------------------------------------------
class CheckInEntrenadorAPIView(APIView):
    # Solo usuarios autenticados pueden usar esta vista
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, actividad_id):
        """
        Endpoint POST: /api/check-in/entrenador/<actividad_id>/
        Recibe lat/lon desde la app y registra la presencia
        """
        # --------------------------------------------------------
        # 1️⃣ Obtenemos el usuario logueado (el entrenador)
        # --------------------------------------------------------
        usuario = request.user

        # --------------------------------------------------------
        # 2️⃣ Obtenemos la actividad correspondiente y su sede
        #    select_related mejora eficiencia al traer la sede en la misma query
        # --------------------------------------------------------
        try:
            actividad = Actividad.objects.select_related('sede').get(id=actividad_id)
        except Actividad.DoesNotExist:
            # Si no existe la actividad, devolvemos error 404
            return Response({"error": "Actividad no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        # Si la actividad no tiene sede asignada
        if not actividad.sede:
            return Response({"error": "Actividad sin sede asignada"}, status=status.HTTP_400_BAD_REQUEST)

        # --------------------------------------------------------
        # 3️⃣ Validamos los datos enviados por la app usando el serializer
        # --------------------------------------------------------
        serializer = PresencialidadEntrenadorSerializer(data=request.data)
        if serializer.is_valid():
            # Extraemos lat/lon validados
            lat = serializer.validated_data['lat']
            lon = serializer.validated_data['lon']

            # Obtenemos la IP del dispositivo que hace la petición
            ip = get_client_ip(request)

            sede = actividad.sede

            # --------------------------------------------------------
            # 4️⃣ Verificamos que el usuario esté dentro del radio permitido de la sede
            # --------------------------------------------------------
            distancia = distancia_metros(lat, lon, sede.lat, sede.lon)
            if distancia > sede.radio_metros:
                return Response(
                    {"error": f"No estás dentro del área permitida de la sede (distancia: {int(distancia)} m)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # --------------------------------------------------------
            # 5️⃣ Verificamos que el usuario no haya registrado ya su presencialidad
            #    Esto evita duplicados
            # --------------------------------------------------------
            if PresencialidadEntrenador.objects.filter(actividad=actividad, usuario=usuario).exists():
                return Response(
                    {"error": "Ya registraste tu presencialidad para esta actividad"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # --------------------------------------------------------
            # 6️⃣ Creamos el registro de presencialidad
            # --------------------------------------------------------
            PresencialidadEntrenador.objects.create(
                actividad=actividad,
                usuario=usuario,
                presente=True,  # marcamos como presente
                lat=lat,
                lon=lon,
                ip=ip
            )

            # --------------------------------------------------------
            # 7️⃣ Respondemos a la app con éxito
            # --------------------------------------------------------
            return Response({"success": "Presencialidad registrada"}, status=status.HTTP_201_CREATED)

        # --------------------------------------------------------
        # 8️⃣ Si los datos enviados no son válidos (faltan lat/lon, etc.)
        #    devolvemos errores del serializer
        # --------------------------------------------------------
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
