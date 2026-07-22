from __future__ import annotations
import flet as ft
import database as db
from components.ui import app_bar, dashboard_card, page_title, snack, stat_card, table

HOME="/medico"
def _u(page): return page.session.get("user") or {}
def _body(*controls):
    return ft.Container(expand=True,padding=24,content=ft.Column(list(controls),spacing=18,scroll=ft.ScrollMode.AUTO,expand=True))

def dashboard(page):
    u=_u(page); agenda=db.get_doctor_agenda(u["medico_id"])
    cards=[
        dashboard_card(page,ft.Icons.CALENDAR_TODAY,"Agenda de hoy","Pacientes y consultas del día.","/medico/agenda",ft.Colors.GREEN),
        dashboard_card(page,ft.Icons.FOLDER_SHARED,"Expedientes","Busca pacientes y revisa sus datos.","/medico/expedientes",ft.Colors.BLUE),
        dashboard_card(page,ft.Icons.VIDEO_CALL,"Telemedicina","Sala virtual para consulta.","/medico/telemedicina",ft.Colors.ORANGE),
        dashboard_card(page,ft.Icons.MEDICATION,"Emitir receta","Registra una receta digital.","/medico/receta",ft.Colors.PURPLE),
        dashboard_card(page,ft.Icons.MONITOR_HEART,"Signos vitales","Datos recientes de pacientes.","/medico/signos",ft.Colors.RED)]
    stats=ft.ResponsiveRow([
        stat_card("Citas de hoy",len(agenda),ft.Icons.EVENT,ft.Colors.GREEN),
        stat_card("En espera",sum(a["estado"]=="en_espera" for a in agenda),ft.Icons.HOURGLASS_TOP,ft.Colors.ORANGE),
        stat_card("Telemedicina",sum(a["modalidad"]=="telemedicina" for a in agenda),ft.Icons.VIDEO_CALL,ft.Colors.BLUE)],spacing=16,run_spacing=16)
    return ft.View(HOME,[_body(page_title(f'Dr./Dra. {u.get("nombre","")} {u.get("apellidos","")}',u.get("especialidad","Portal médico")),stats,ft.ResponsiveRow(cards,spacing=16,run_spacing=16))],appbar=app_bar(page,"Clínica-Digital · Portal Médico","medico",HOME))

def agenda_view(page):
    data=db.get_doctor_agenda(_u(page)["medico_id"])
    agenda=table(["Hora","Paciente","Motivo","Modalidad","Estado"],[[a["hora"],a["paciente"],a["motivo"],a["modalidad"],a["estado"]] for a in data])
    return ft.View("/medico/agenda",[_body(page_title("Agenda de hoy","Citas asignadas al médico."),agenda)],appbar=app_bar(page,"Agenda médica","medico",HOME,True))

def records_view(page):
    search=ft.TextField(label="Buscar paciente",prefix_icon=ft.Icons.SEARCH)
    holder=ft.Column()
    def load(_=None):
        pts=db.list_patients(search.value or "")
        holder.controls=[table(["ID","Nombre","Correo","Teléfono","Nacimiento","Sangre","Alergias"],[[p["id"],p["nombre"],p["correo"],p["telefono"],p["fecha_nac"],p["tipo_sangre"],p["alergias"]] for p in pts])]
        page.update()
    load()
    bar=ft.ResponsiveRow([ft.Container(search,col={"xs":12,"md":9}),ft.Container(ft.FilledButton("Buscar",icon=ft.Icons.SEARCH,on_click=load),col={"xs":12,"md":3})])
    return ft.View("/medico/expedientes",[_body(page_title("Gestión de expedientes","Busca pacientes y consulta sus datos."),bar,holder)],appbar=app_bar(page,"Expedientes","medico",HOME,True))

def telemedicine_view(page):
    notes=ft.TextField(label="Notas de consulta",multiline=True,min_lines=7)
    def save(_):
        if not notes.value or not notes.value.strip(): snack(page,"Escribe notas de consulta.",True); return
        snack(page,"Notas guardadas en la demostración.")
    left=ft.Container(col={"xs":12,"lg":4},padding=20,border_radius=16,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        ft.Text("Datos del paciente",size=20,weight=ft.FontWeight.BOLD),ft.Text("Selecciona la cita activa desde la agenda."),notes,ft.FilledButton("Guardar notas",icon=ft.Icons.SAVE,on_click=save)]))
    right=ft.Container(col={"xs":12,"lg":8},padding=20,border_radius=16,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        page_title("Videoconsulta","Sala virtual del médico."),ft.Container(height=380,bgcolor=ft.Colors.BLACK87,border_radius=14,alignment=ft.alignment.center,content=ft.Icon(ft.Icons.VIDEOCAM,size=80,color=ft.Colors.WHITE)),
        ft.Row([ft.IconButton(ft.Icons.MIC),ft.IconButton(ft.Icons.VIDEOCAM),ft.FilledButton("Finalizar",icon=ft.Icons.CALL_END,bgcolor=ft.Colors.RED,on_click=lambda _:snack(page,"Consulta finalizada."))],alignment=ft.MainAxisAlignment.CENTER,wrap=True)]))
    return ft.View("/medico/telemedicina",[_body(ft.ResponsiveRow([left,right],spacing=16,run_spacing=16))],appbar=app_bar(page,"Telemedicina médica","medico",HOME,True))

def prescription_view(page):
    pts=db.list_patients()
    patient=ft.Dropdown(label="Paciente",options=[ft.dropdown.Option(str(p["id"]),p["nombre"]) for p in pts])
    medication=ft.TextField(label="Medicamento"); dose=ft.TextField(label="Dosis"); frequency=ft.TextField(label="Frecuencia"); duration=ft.TextField(label="Duración"); instructions=ft.TextField(label="Indicaciones",multiline=True,min_lines=3)
    def save(_):
        if not patient.value: snack(page,"Selecciona un paciente.",True); return
        if not medication.value or not medication.value.strip(): snack(page,"Escribe el medicamento.",True); return
        db.create_prescription(_u(page)["medico_id"],int(patient.value),medication.value,dose.value or "",frequency.value or "",duration.value or "",instructions.value or "")
        snack(page,"Receta emitida correctamente.")
        patient.value=None
        for c in [medication,dose,frequency,duration,instructions]: c.value=""
        page.update()
    form=ft.Container(width=760,padding=28,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([
        page_title("Emitir receta digital","La receta quedará vinculada al paciente."),patient,medication,
        ft.ResponsiveRow([ft.Container(dose,col={"xs":12,"md":4}),ft.Container(frequency,col={"xs":12,"md":4}),ft.Container(duration,col={"xs":12,"md":4})]),instructions,
        ft.FilledButton("Emitir receta",icon=ft.Icons.MEDICATION,on_click=save)]))
    return ft.View("/medico/receta",[_body(ft.Row([form],alignment=ft.MainAxisAlignment.CENTER))],appbar=app_bar(page,"Nueva receta","medico",HOME,True))

def vitals_view(page):
    data=db.get_latest_vitals()
    vitals=table(["Fecha","Paciente","Temperatura","Presión","FC","O₂","Síntomas"],[[r["registrado_en"],r["paciente"],r["temperatura"],r["presion"],r["frec_cardiaca"],r["saturacion_o2"],r["sintomas"]] for r in data])
    return ft.View("/medico/signos",[_body(page_title("Signos vitales recibidos","Registros recientes enviados por pacientes."),vitals)],appbar=app_bar(page,"Signos vitales","medico",HOME,True))