from __future__ import annotations
import flet as ft
import database as db
from components.ui import app_bar, dashboard_card, page_title, snack, table, stat_card

HOME="/medico"
def _u(page): return page.session.get("user") or {}

def dashboard(page: ft.Page)->ft.View:
    u=_u(page); agenda=db.get_doctor_agenda(u["medico_id"])
    cards=[dashboard_card(page,ft.Icons.CALENDAR_TODAY,"Agenda de hoy","Pacientes y consultas del día.","/medico/agenda",ft.Colors.GREEN),dashboard_card(page,ft.Icons.FOLDER_SHARED,"Expedientes","Busca pacientes y revisa sus datos.","/medico/expedientes",ft.Colors.BLUE),dashboard_card(page,ft.Icons.VIDEO_CALL,"Telemedicina","Sala virtual para consulta.","/medico/telemedicina",ft.Colors.ORANGE),dashboard_card(page,ft.Icons.MEDICATION,"Emitir receta","Registra una receta digital.","/medico/receta",ft.Colors.PURPLE),dashboard_card(page,ft.Icons.MONITOR_HEART,"Signos vitales","Datos recientes de pacientes.","/medico/signos",ft.Colors.RED)]
    return ft.View(HOME,[ft.Container(padding=24,content=ft.Column([page_title(f'Dr./Dra. {u.get("nombre","")} {u.get("apellidos","")}',u.get("especialidad", "Portal médico")),ft.ResponsiveRow([stat_card("Citas de hoy",len(agenda),ft.Icons.EVENT,ft.Colors.GREEN),stat_card("En espera",sum(a["estado"]=="en_espera" for a in agenda),ft.Icons.HOURGLASS_TOP,ft.Colors.ORANGE),stat_card("Telemedicina",sum(a["modalidad"]=="telemedicina" for a in agenda),ft.Icons.VIDEO_CALL,ft.Colors.BLUE)]),ft.ResponsiveRow(cards,spacing=16,run_spacing=16)],scroll=ft.ScrollMode.ALWAYS))],appbar=app_bar(page,"Clínica-Digital · Portal Médico","medico",HOME),scroll=ft.ScrollMode.ALWAYS)

def agenda_view(page):
    data=db.get_doctor_agenda(_u(page)["medico_id"])
    return ft.View("/medico/agenda",[ft.Container(padding=24,content=ft.Column([page_title("Agenda de hoy","Citas asignadas al médico."),table(["Hora","Paciente","Motivo","Modalidad","Estado"],[[a["hora"],a["paciente"],a["motivo"],a["modalidad"],a["estado"]] for a in data])]))],appbar=app_bar(page,"Agenda médica","medico",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def records_view(page):
    search=ft.TextField(label="Buscar paciente",prefix_icon=ft.Icons.SEARCH,expand=True)
    holder=ft.Column()
    def load(_=None):
        pts=db.list_patients(search.value or "")
        holder.controls=[table(["ID","Nombre","Correo","Teléfono","Sangre","Alergias"],[[p["id"],p["nombre"],p["correo"],p["telefono"],p["tipo_sangre"],p["alergias"]] for p in pts])]
        page.update()
    load()
    return ft.View("/medico/expedientes",[ft.Container(padding=24,content=ft.Column([page_title("Gestión de expedientes","Búsqueda de pacientes."),ft.Row([search,ft.FilledButton("Buscar",icon=ft.Icons.SEARCH,on_click=load)]),holder]))],appbar=app_bar(page,"Expedientes","medico",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def telemedicine_view(page):
    return ft.View("/medico/telemedicina",[ft.Container(padding=24,content=ft.ResponsiveRow([ft.Container(col={"xs":12,"lg":3},padding=20,border_radius=16,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([ft.Text("Datos del paciente",size=20,weight=ft.FontWeight.BOLD),ft.Text("Selecciona la cita activa desde la agenda."),ft.TextField(label="Notas de consulta",multiline=True,min_lines=8),ft.FilledButton("Guardar notas",icon=ft.Icons.SAVE,on_click=lambda _:snack(page,"Notas guardadas localmente en la interfaz."))])),ft.Container(col={"xs":12,"lg":9},padding=20,border_radius=16,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([page_title("Videoconsulta","Integra aquí tu servidor WebRTC."),ft.Container(height=380,bgcolor=ft.Colors.BLACK87,border_radius=14,alignment=ft.alignment.center,content=ft.Icon(ft.Icons.VIDEOCAM,size=80,color=ft.Colors.WHITE)),ft.Row([ft.IconButton(ft.Icons.MIC),ft.IconButton(ft.Icons.VIDEOCAM),ft.FilledButton("Finalizar",icon=ft.Icons.CALL_END,bgcolor=ft.Colors.RED)],alignment=ft.MainAxisAlignment.CENTER)]))],spacing=16,run_spacing=16))],appbar=app_bar(page,"Telemedicina médica","medico",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def prescription_view(page):
    pts=db.list_patients(); patient=ft.Dropdown(label="Paciente",options=[ft.dropdown.Option(str(p["id"]),p["nombre"]) for p in pts]); medication=ft.TextField(label="Medicamento"); dose=ft.TextField(label="Dosis"); frequency=ft.TextField(label="Frecuencia"); duration=ft.TextField(label="Duración"); instructions=ft.TextField(label="Indicaciones",multiline=True,min_lines=3)
    def save(_):
        if not patient.value or not medication.value: snack(page,"Selecciona paciente y medicamento.",True); return
        db.create_prescription(_u(page)["medico_id"],int(patient.value),medication.value,dose.value,frequency.value,duration.value,instructions.value); snack(page,"Receta emitida correctamente.")
        for c in [medication,dose,frequency,duration,instructions]: c.value=""
        page.update()
    form=ft.Container(max_width=720,padding=28,border_radius=18,bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,content=ft.Column([page_title("Emitir receta digital","La receta quedará vinculada al paciente."),patient,medication,ft.ResponsiveRow([ft.Container(dose,col=6),ft.Container(frequency,col=6),ft.Container(duration,col=6)]),instructions,ft.FilledButton("Emitir receta",icon=ft.Icons.MEDICATION,on_click=save)]))
    return ft.View("/medico/receta",[ft.Container(form,padding=24,alignment=ft.alignment.top_center)],appbar=app_bar(page,"Nueva receta","medico",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def vitals_view(page):
    data=db.get_latest_vitals()
    return ft.View("/medico/signos",[ft.Container(padding=24,content=ft.Column([page_title("Signos vitales recibidos","Registros recientes de pacientes."),table(["Fecha","Paciente","Temp.","Presión","FC","O₂","Síntomas"],[[r["registrado_en"],r["paciente"],r["temperatura"],r["presion"],r["frec_cardiaca"],r["saturacion_o2"],r["sintomas"]] for r in data])]))],appbar=app_bar(page,"Signos vitales","medico",HOME,True),scroll=ft.ScrollMode.ALWAYS)