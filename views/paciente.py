from __future__ import annotations
from datetime import date, timedelta
import flet as ft
import database as db
from components.ui import app_bar, dashboard_card, page_title, snack, table

HOME = "/paciente"


def _user(page: ft.Page) -> dict:
    return page.session.get("user") or {}


def dashboard(page: ft.Page) -> ft.View:
    u = _user(page)
    cards = [
        dashboard_card(page, ft.Icons.CALENDAR_MONTH, "Agendar cita", "Programa una consulta médica.", "/paciente/agendar", ft.Colors.BLUE),
        dashboard_card(page, ft.Icons.EVENT_NOTE, "Mis citas", "Consulta próximas citas e historial.", "/paciente/citas", ft.Colors.GREEN),
        dashboard_card(page, ft.Icons.FOLDER_SHARED, "Expediente", "Consulta diagnósticos y recetas.", "/paciente/expediente", ft.Colors.ORANGE),
        dashboard_card(page, ft.Icons.VIDEO_CALL, "Telemedicina", "Entra a tu consulta virtual.", "/paciente/telemedicina", ft.Colors.RED),
        dashboard_card(page, ft.Icons.HOURGLASS_TOP, "Cola virtual", "Consulta tu turno de atención.", "/paciente/cola", ft.Colors.PURPLE),
        dashboard_card(page, ft.Icons.FAVORITE, "Signos vitales", "Registra datos antes de consulta.", "/paciente/signos", ft.Colors.PINK),
    ]
    appts = db.get_patient_appointments(u["id"])
    upcoming = next((a for a in reversed(appts) if a["estado"] in ("confirmada", "en_espera")), None)
    next_card = ft.Container(
        width=300, padding=20, border_radius=18, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([
            ft.Text("Próxima cita", size=20, weight=ft.FontWeight.BOLD), ft.Divider(),
            ft.Text(upcoming["medico"] if upcoming else "Sin citas programadas", weight=ft.FontWeight.BOLD),
            ft.Text(upcoming["especialidad"] if upcoming else ""),
            ft.Text(f'{upcoming["fecha"]} · {upcoming["hora"]}' if upcoming else "", color=ft.Colors.BLUE_700),
            ft.Text(upcoming["modalidad"].title() if upcoming else ""),
        ])
    )
    return ft.View(HOME, [
        ft.Row([
            ft.Container(expand=True, padding=24, content=ft.Column([
                page_title(f"Bienvenido/a, {u.get('nombre','Paciente')} 👋", "¿Qué deseas hacer hoy?"),
                ft.ResponsiveRow(cards, spacing=16, run_spacing=16),
            ], scroll=ft.ScrollMode.AUTO)),
            ft.Container(next_card, padding=20, visible=page.width is None or page.width > 900),
        ], expand=True)
    ], appbar=app_bar(page, "Clínica-Digital · Portal Paciente", "paciente", HOME), scroll=ft.ScrollMode.ALWAYS)


def appointment_view(page: ft.Page) -> ft.View:
    u = _user(page); doctors = db.list_doctors()
    doctor = ft.Dropdown(label="Médico", options=[ft.dropdown.Option(str(d["id"]), f'{d["nombre"]} · {d["especialidad"]}') for d in doctors], value=str(doctors[0]["id"]) if doctors else None)
    modality = ft.Dropdown(label="Modalidad", options=[ft.dropdown.Option("presencial", "Presencial"), ft.dropdown.Option("telemedicina", "Telemedicina")], value="presencial")
    appointment_date = ft.TextField(label="Fecha (AAAA-MM-DD)", value=str(date.today() + timedelta(days=1)), prefix_icon=ft.Icons.DATE_RANGE)
    hour = ft.Dropdown(label="Hora", options=[ft.dropdown.Option(h) for h in ["09:00","09:30","10:00","10:30","11:00","11:30","12:00","16:00","16:30","17:00"]], value="09:00")
    reason = ft.TextField(label="Motivo de consulta", multiline=True, min_lines=3, max_lines=5)

    def reserve(_):
        try:
            date.fromisoformat(appointment_date.value)
            if not reason.value.strip(): raise ValueError("Escribe el motivo de consulta.")
            ok, msg = db.reserve_appointment(u["id"], int(doctor.value), appointment_date.value, hour.value, modality.value, reason.value)
            snack(page, msg, not ok)
            if ok: page.go("/paciente/citas")
        except ValueError as ex: snack(page, str(ex) or "Revisa los datos.", True)

    form = ft.Container(max_width=760, padding=28, border_radius=18, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([page_title("Agendar nueva cita", "Selecciona médico, fecha, horario y modalidad."), doctor, modality,
                           ft.ResponsiveRow([ft.Container(appointment_date, col={"xs":12,"md":6}), ft.Container(hour, col={"xs":12,"md":6})]),
                           reason, ft.Row([ft.OutlinedButton("Volver", on_click=lambda _: page.go(HOME)), ft.FilledButton("Confirmar cita", icon=ft.Icons.CHECK, on_click=reserve)], alignment=ft.MainAxisAlignment.END)]))
    return ft.View("/paciente/agendar", [ft.Container(form, padding=24, alignment=ft.alignment.top_center)], appbar=app_bar(page,"Agendar cita","paciente",HOME,True), scroll=ft.ScrollMode.AUTO)


def appointments_view(page: ft.Page) -> ft.View:
    u = _user(page); data = db.get_patient_appointments(u["id"])
    selected = ft.TextField(visible=False)
    rows = []
    for a in data:
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(a["fecha"])), ft.DataCell(ft.Text(a["hora"])), ft.DataCell(ft.Text(a["medico"])),
            ft.DataCell(ft.Text(a["especialidad"])), ft.DataCell(ft.Text(a["modalidad"].title())), ft.DataCell(ft.Text(a["estado"].replace("_"," ").title())),
            ft.DataCell(ft.IconButton(ft.Icons.CANCEL_OUTLINED, tooltip="Cancelar", disabled=a["estado"] not in ("confirmada","en_espera"), on_click=lambda _, aid=a["id"]: cancel(aid)))
        ]))
    dt = ft.DataTable(columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in ["Fecha","Hora","Médico","Especialidad","Modalidad","Estado","Acción"]], rows=rows)
    def cancel(aid: int):
        if db.cancel_appointment(aid, u["id"]): snack(page,"Cita cancelada."); page.go("/paciente/citas")
        else: snack(page,"No se pudo cancelar la cita.",True)
    return ft.View("/paciente/citas", [ft.Container(padding=24, content=ft.Column([page_title("Mis citas","Historial y citas programadas."), ft.Row([dt], scroll=ft.ScrollMode.ALWAYS), selected], scroll=ft.ScrollMode.AUTO))], appbar=app_bar(page,"Mis citas","paciente",HOME,True), scroll=ft.ScrollMode.ALWAYS)


def record_view(page: ft.Page) -> ft.View:
    u = _user(page); records=db.get_patient_record(u["id"]); prescriptions=db.get_patient_prescriptions(u["id"])
    profile = ft.Container(width=280,padding=20,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        ft.Text("Mi perfil médico",size=20,weight=ft.FontWeight.BOLD),ft.Divider(),
        ft.Text(f'{u.get("nombre","")} {u.get("apellidos","")}',weight=ft.FontWeight.BOLD),
        ft.Text(f'Fecha nac.: {u.get("fecha_nac") or "—"}'),ft.Text(f'Tipo de sangre: {u.get("tipo_sangre") or "—"}'),ft.Text(f'Alergias: {u.get("alergias") or "—"}')]))
    visits=table(["Fecha","Médico","Diagnóstico","Notas"],[[r["fecha_visita"],r["medico"],r["diagnostico"],r["notas"]] for r in records])
    meds=table(["Fecha","Medicamento","Dosis","Frecuencia","Duración","Médico"],[[r["fecha_emision"],r["medicamento"],r["dosis"],r["frecuencia"],r["duracion"],r["medico"]] for r in prescriptions])
    tabs=ft.Tabs(selected_index=0,tabs=[ft.Tab(text="Visitas",icon=ft.Icons.HISTORY,content=ft.Container(visits,padding=12)),ft.Tab(text="Recetas",icon=ft.Icons.MEDICATION,content=ft.Container(meds,padding=12))],expand=True)
    return ft.View("/paciente/expediente",[ft.Container(padding=20,content=ft.ResponsiveRow([ft.Container(profile,col={"xs":12,"lg":3}),ft.Container(ft.Column([page_title("Expediente clínico","Historial de visitas, diagnósticos y recetas."),tabs]),col={"xs":12,"lg":9})],spacing=16,run_spacing=16))],appbar=app_bar(page,"Expediente clínico","paciente",HOME,True),scroll=ft.ScrollMode.ALWAYS)


def telemedicine_view(page: ft.Page) -> ft.View:
    return ft.View("/paciente/telemedicina",[ft.Container(padding=24,alignment=ft.alignment.top_center,content=ft.Container(max_width=850,padding=24,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        page_title("Telemedicina","Demostración visual; conecta aquí tu proveedor WebRTC."),
        ft.Container(height=340,bgcolor=ft.Colors.BLACK87,border_radius=14,alignment=ft.alignment.center,content=ft.Column([ft.Icon(ft.Icons.VIDEOCAM,size=70,color=ft.Colors.WHITE),ft.Text("Área de videollamada",size=22,color=ft.Colors.WHITE),ft.Text("Conectado · latencia simulada 48 ms",color=ft.Colors.GREEN_300)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER)),
        ft.Row([ft.IconButton(ft.Icons.MIC,tooltip="Micrófono"),ft.IconButton(ft.Icons.VIDEOCAM,tooltip="Cámara"),ft.FilledButton("Colgar",icon=ft.Icons.CALL_END,bgcolor=ft.Colors.RED,on_click=lambda _: snack(page,"Llamada finalizada."))],alignment=ft.MainAxisAlignment.CENTER),
        ft.TextField(label="Mensaje para el médico",suffix_icon=ft.Icons.SEND)
    ])))],appbar=app_bar(page,"Telemedicina","paciente",HOME,True),scroll=ft.ScrollMode.AUTO)


def queue_view(page: ft.Page) -> ft.View:
    q=db.get_queue_for_patient(_user(page)["id"])
    content = [page_title("Cola de espera virtual","Consulta tu posición para la atención presencial.")]
    if q:
        content += [ft.Text(f'#{q["turno"]}',size=72,weight=ft.FontWeight.BOLD,color=ft.Colors.PURPLE),ft.Text(f'Estado: {q["estado"].replace("_"," ").title()}',size=18),ft.ProgressBar(value=.7),ft.Text("Tiempo estimado: ~10 minutos",color=ft.Colors.ORANGE_700)]
    else: content += [ft.Icon(ft.Icons.CHECK_CIRCLE,size=72,color=ft.Colors.GREEN),ft.Text("No tienes un turno activo.",size=20)]
    return ft.View("/paciente/cola",[ft.Container(expand=True,alignment=ft.alignment.center,content=ft.Container(width=560,padding=35,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column(content,horizontal_alignment=ft.CrossAxisAlignment.CENTER)))],appbar=app_bar(page,"Cola virtual","paciente",HOME,True),scroll=ft.ScrollMode.ALWAYS)


def vitals_view(page: ft.Page) -> ft.View:
    fields={
        "temperatura":ft.TextField(label="Temperatura °C",value="36.6"),"sistolica":ft.TextField(label="Presión sistólica",value="120"),
        "diastolica":ft.TextField(label="Presión diastólica",value="80"),"cardiaca":ft.TextField(label="Frecuencia cardíaca",value="72"),
        "saturacion":ft.TextField(label="Saturación O₂ %",value="98"),"peso":ft.TextField(label="Peso kg",value="74"),
        "sintomas":ft.TextField(label="Síntomas",multiline=True,min_lines=3)
    }
    def save(_):
        try:
            data={"temperatura":float(fields["temperatura"].value),"sistolica":int(fields["sistolica"].value),"diastolica":int(fields["diastolica"].value),"cardiaca":int(fields["cardiaca"].value),"saturacion":float(fields["saturacion"].value),"peso":float(fields["peso"].value),"sintomas":fields["sintomas"].value}
            db.save_vitals(_user(page)["id"],data); snack(page,"Signos vitales guardados."); page.go(HOME)
        except ValueError: snack(page,"Usa valores numéricos válidos.",True)
    grid=ft.ResponsiveRow([ft.Container(v,col={"xs":12,"md":6}) for k,v in fields.items() if k!="sintomas"])
    form=ft.Container(max_width=760,padding=28,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([page_title("Signos vitales preconsulta","El médico podrá ver estos datos."),grid,fields["sintomas"],ft.FilledButton("Guardar y enviar",icon=ft.Icons.SAVE,on_click=save)]))
    return ft.View("/paciente/signos",[ft.Container(form,padding=24,alignment=ft.alignment.top_center)],appbar=app_bar(page,"Signos vitales","paciente",HOME,True),scroll=ft.ScrollMode.AUTO)