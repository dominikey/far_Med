from __future__ import annotations
from datetime import date, timedelta
import flet as ft
import database as db
from components.ui import app_bar, dashboard_card, page_title, snack, table

HOME="/paciente"
def _u(page): return page.session.get("user") or {}
def _body(*controls):
    return ft.Container(expand=True,padding=24,content=ft.Column(list(controls),spacing=18,scroll=ft.ScrollMode.AUTO,expand=True))

def dashboard(page):
    u=_u(page)
    cards=[
        dashboard_card(page,ft.Icons.CALENDAR_MONTH,"Agendar cita","Programa una consulta médica.","/paciente/agendar",ft.Colors.BLUE),
        dashboard_card(page,ft.Icons.EVENT_NOTE,"Mis citas","Consulta próximas citas e historial.","/paciente/citas",ft.Colors.GREEN),
        dashboard_card(page,ft.Icons.FOLDER_SHARED,"Expediente","Consulta diagnósticos y recetas.","/paciente/expediente",ft.Colors.ORANGE),
        dashboard_card(page,ft.Icons.VIDEO_CALL,"Telemedicina","Entra a tu consulta virtual.","/paciente/telemedicina",ft.Colors.RED),
        dashboard_card(page,ft.Icons.HOURGLASS_TOP,"Cola virtual","Consulta tu turno.","/paciente/cola",ft.Colors.PURPLE),
        dashboard_card(page,ft.Icons.FAVORITE,"Signos vitales","Registra datos antes de consulta.","/paciente/signos",ft.Colors.PINK)]
    return ft.View(HOME,[_body(page_title(f"Bienvenido/a, {u.get('nombre','Paciente')} 👋","¿Qué deseas hacer hoy?"),ft.ResponsiveRow(cards,spacing=16,run_spacing=16))],appbar=app_bar(page,"Clínica-Digital · Portal Paciente","paciente",HOME))

def appointment_view(page):
    u=_u(page); doctors=db.list_doctors()
    doctor=ft.Dropdown(label="Médico",options=[ft.dropdown.Option(str(d["id"]),f'{d["nombre"]} · {d["especialidad"]}') for d in doctors],value=str(doctors[0]["id"]) if doctors else None)
    modality=ft.Dropdown(label="Modalidad",options=[ft.dropdown.Option("presencial","Presencial"),ft.dropdown.Option("telemedicina","Telemedicina")],value="presencial")
    fecha=ft.TextField(label="Fecha (AAAA-MM-DD)",value=str(date.today()+timedelta(days=1)),prefix_icon=ft.Icons.DATE_RANGE)
    hora=ft.Dropdown(label="Hora",options=[ft.dropdown.Option(h) for h in ["09:00","09:30","10:00","10:30","11:00","11:30","12:00","16:00","16:30","17:00"]],value="09:00")
    motivo=ft.TextField(label="Motivo de consulta",multiline=True,min_lines=3)
    def guardar(_):
        try:
            if not doctor.value: raise ValueError("Selecciona un médico.")
            if date.fromisoformat(fecha.value)<date.today(): raise ValueError("La fecha no puede estar en el pasado.")
            if not motivo.value or not motivo.value.strip(): raise ValueError("Escribe el motivo.")
            ok,msg=db.reserve_appointment(u["id"],int(doctor.value),fecha.value,hora.value,modality.value,motivo.value)
            snack(page,msg,not ok)
            if ok: page.go("/paciente/citas")
        except ValueError as ex: snack(page,str(ex),True)
    form=ft.Container(width=760,padding=28,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        page_title("Agendar nueva cita","Selecciona médico, fecha, horario y modalidad."),doctor,modality,
        ft.ResponsiveRow([ft.Container(fecha,col={"xs":12,"md":6}),ft.Container(hora,col={"xs":12,"md":6})]),motivo,
        ft.Row([ft.OutlinedButton("Volver",on_click=lambda _:page.go(HOME)),ft.FilledButton("Confirmar cita",icon=ft.Icons.CHECK,on_click=guardar)],alignment=ft.MainAxisAlignment.END,wrap=True)]))
    return ft.View("/paciente/agendar",[_body(ft.Row([form],alignment=ft.MainAxisAlignment.CENTER))],appbar=app_bar(page,"Agendar cita","paciente",HOME,True))

def appointments_view(page):
    u=_u(page); data=db.get_patient_appointments(u["id"])
    def cancelar(aid):
        if db.cancel_appointment(aid,u["id"]): snack(page,"Cita cancelada."); page.go("/paciente/citas")
        else: snack(page,"No se pudo cancelar.",True)
    rows=[]
    for a in data:
        rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(a[k]))) for k in ["fecha","hora","medico","especialidad","modalidad","estado"]]+[
            ft.DataCell(ft.IconButton(ft.Icons.CANCEL_OUTLINED,disabled=a["estado"] not in ("confirmada","en_espera"),on_click=lambda _,aid=a["id"]:cancelar(aid)))]))
    dt=ft.DataTable(columns=[ft.DataColumn(ft.Text(c,weight=ft.FontWeight.BOLD)) for c in ["Fecha","Hora","Médico","Especialidad","Modalidad","Estado","Acción"]],rows=rows)
    return ft.View("/paciente/citas",[_body(page_title("Mis citas","Historial y citas programadas."),ft.Row([dt],scroll=ft.ScrollMode.AUTO))],appbar=app_bar(page,"Mis citas","paciente",HOME,True))

def record_view(page):
    u=_u(page); rec=db.get_patient_record(u["id"]); meds=db.get_patient_prescriptions(u["id"])
    profile=ft.Container(padding=20,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        ft.Text("Mi perfil médico",size=20,weight=ft.FontWeight.BOLD),ft.Divider(),ft.Text(f'{u.get("nombre","")} {u.get("apellidos","")}',weight=ft.FontWeight.BOLD),
        ft.Text(f'Fecha de nacimiento: {u.get("fecha_nac") or "—"}'),ft.Text(f'Tipo de sangre: {u.get("tipo_sangre") or "—"}'),ft.Text(f'Alergias: {u.get("alergias") or "—"}')]))
    visits=table(["Fecha","Médico","Diagnóstico","Notas"],[[r["fecha_visita"],r["medico"],r["diagnostico"],r["notas"]] for r in rec])
    prescriptions=table(["Fecha","Medicamento","Dosis","Frecuencia","Duración","Médico"],[[r["fecha_emision"],r["medicamento"],r["dosis"],r["frecuencia"],r["duracion"],r["medico"]] for r in meds])
    content=ft.ResponsiveRow([ft.Container(profile,col={"xs":12,"lg":3}),ft.Container(ft.Column([page_title("Expediente clínico","Historial de consultas y recetas."),ft.Text("Consultas",size=20,weight=ft.FontWeight.BOLD),visits,ft.Divider(),ft.Text("Recetas",size=20,weight=ft.FontWeight.BOLD),prescriptions]),col={"xs":12,"lg":9})],spacing=16,run_spacing=16)
    return ft.View("/paciente/expediente",[_body(content)],appbar=app_bar(page,"Expediente clínico","paciente",HOME,True))

def telemedicine_view(page):
    panel=ft.Container(width=850,padding=24,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        page_title("Telemedicina","Sala virtual de consulta."),ft.Container(height=340,bgcolor=ft.Colors.BLACK87,border_radius=14,alignment=ft.alignment.center,content=ft.Column([
            ft.Icon(ft.Icons.VIDEOCAM,size=70,color=ft.Colors.WHITE),ft.Text("Área de videollamada",size=22,color=ft.Colors.WHITE)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER)),
        ft.Row([ft.IconButton(ft.Icons.MIC),ft.IconButton(ft.Icons.VIDEOCAM),ft.FilledButton("Colgar",icon=ft.Icons.CALL_END,bgcolor=ft.Colors.RED,on_click=lambda _:snack(page,"Llamada finalizada."))],alignment=ft.MainAxisAlignment.CENTER,wrap=True),
        ft.TextField(label="Mensaje para el médico",multiline=True,min_lines=2)]))
    return ft.View("/paciente/telemedicina",[_body(ft.Row([panel],alignment=ft.MainAxisAlignment.CENTER))],appbar=app_bar(page,"Telemedicina","paciente",HOME,True))

def queue_view(page):
    q=db.get_queue_for_patient(_u(page)["id"]); controls=[page_title("Cola de espera virtual","Consulta tu posición.")]
    if q: controls += [ft.Text(f'#{q["turno"]}',size=72,weight=ft.FontWeight.BOLD),ft.Text(q["estado"])]
    else: controls += [ft.Icon(ft.Icons.CHECK_CIRCLE,size=72,color=ft.Colors.GREEN),ft.Text("No tienes un turno activo.")]
    return ft.View("/paciente/cola",[_body(ft.Container(width=560,padding=30,content=ft.Column(controls,horizontal_alignment=ft.CrossAxisAlignment.CENTER)))],appbar=app_bar(page,"Cola virtual","paciente",HOME,True))

def vitals_view(page):
    f={"temperatura":ft.TextField(label="Temperatura °C",value="36.6"),"sistolica":ft.TextField(label="Presión sistólica",value="120"),"diastolica":ft.TextField(label="Presión diastólica",value="80"),"cardiaca":ft.TextField(label="Frecuencia cardíaca",value="72"),"saturacion":ft.TextField(label="Saturación O₂ %",value="98"),"peso":ft.TextField(label="Peso kg",value="74"),"sintomas":ft.TextField(label="Síntomas",multiline=True,min_lines=3)}
    def guardar(_):
        try:
            db.save_vitals(_u(page)["id"],{"temperatura":float(f["temperatura"].value),"sistolica":int(f["sistolica"].value),"diastolica":int(f["diastolica"].value),"cardiaca":int(f["cardiaca"].value),"saturacion":float(f["saturacion"].value),"peso":float(f["peso"].value),"sintomas":f["sintomas"].value or ""})
            snack(page,"Signos vitales guardados."); page.go(HOME)
        except (TypeError,ValueError): snack(page,"Usa valores numéricos válidos.",True)
    grid=ft.ResponsiveRow([ft.Container(v,col={"xs":12,"md":6}) for k,v in f.items() if k!="sintomas"])
    form=ft.Container(width=760,padding=28,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([page_title("Signos vitales preconsulta","El médico podrá consultar estos datos."),grid,f["sintomas"],ft.FilledButton("Guardar y enviar",icon=ft.Icons.SAVE,on_click=guardar)]))
    return ft.View("/paciente/signos",[_body(ft.Row([form],alignment=ft.MainAxisAlignment.CENTER))],appbar=app_bar(page,"Signos vitales","paciente",HOME,True))