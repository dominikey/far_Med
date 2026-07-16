from __future__ import annotations
import flet as ft
import database as db
from components.ui import app_bar,dashboard_card,page_title,snack,stat_card,table
HOME="/admin"

def dashboard(page):
    k=db.get_kpis(); cards=[dashboard_card(page,ft.Icons.EVENT_NOTE,"Gestión de citas","Consulta todas las citas.","/admin/citas",ft.Colors.BLUE),dashboard_card(page,ft.Icons.QUERY_STATS,"KPIs","Indicadores operativos.","/admin/kpis",ft.Colors.GREEN),dashboard_card(page,ft.Icons.PEOPLE_ALT,"Cola en tiempo real","Gestiona turnos y prioridades.","/admin/cola",ft.Colors.ORANGE),dashboard_card(page,ft.Icons.PERSON_SEARCH,"Pacientes","Directorio de pacientes.","/admin/pacientes",ft.Colors.PURPLE),dashboard_card(page,ft.Icons.NOTIFICATIONS_ACTIVE,"Notificaciones","Recordatorios y envíos.","/admin/notificaciones",ft.Colors.RED)]
    return ft.View(HOME,[ft.Container(padding=24,content=ft.Column([page_title("Recepción / Dirección","Panel operativo de Clínica-Digital"),ft.ResponsiveRow([stat_card("Citas hoy",k["citas_hoy"],ft.Icons.EVENT,ft.Colors.BLUE),stat_card("En espera",k["en_espera"],ft.Icons.HOURGLASS_TOP,ft.Colors.ORANGE),stat_card("Pacientes",k["pacientes"],ft.Icons.PEOPLE,ft.Colors.GREEN)]),ft.ResponsiveRow(cards,spacing=16,run_spacing=16)],scroll=ft.ScrollMode.ALWAYS))],appbar=app_bar(page,"Clínica-Digital · Recepción","admin",HOME),scroll=ft.ScrollMode.ALWAYS)

def appointments_view(page):
    d=db.get_all_appointments()
    return ft.View("/admin/citas",[ft.Container(padding=24,content=ft.Column([page_title("Gestión de citas","Agenda general de la clínica."),table(["Fecha","Hora","Paciente","Médico","Especialidad","Modalidad","Estado"],[[x["fecha"],x["hora"],x["paciente"],x["medico"],x["especialidad"],x["modalidad"],x["estado"]] for x in d])]))],appbar=app_bar(page,"Citas","admin",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def kpis_view(page):
    k=db.get_kpis(); items=[("Citas de hoy",k["citas_hoy"],ft.Icons.EVENT,ft.Colors.BLUE),("Completadas",k["completadas"],ft.Icons.CHECK_CIRCLE,ft.Colors.GREEN),("En espera",k["en_espera"],ft.Icons.HOURGLASS_TOP,ft.Colors.ORANGE),("No-show",k["no_show"],ft.Icons.PERSON_OFF,ft.Colors.RED),("Pacientes",k["pacientes"],ft.Icons.PEOPLE,ft.Colors.PURPLE),("Telemedicina",k["telemedicina"],ft.Icons.VIDEO_CALL,ft.Colors.CYAN)]
    return ft.View("/admin/kpis",[ft.Container(padding=24,content=ft.Column([page_title("Indicadores operativos","Resumen actualizado desde SQLite."),ft.ResponsiveRow([stat_card(*x) for x in items],spacing=16,run_spacing=16)]))],appbar=app_bar(page,"KPIs","admin",HOME,True))

def queue_view(page):
    holder=ft.Column()
    def load():
        q=db.get_queue(); rows=[]
        for x in q:
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(x["turno"]))),ft.DataCell(ft.Text(x["paciente"])),ft.DataCell(ft.Text(x["medico"])),ft.DataCell(ft.Text(x["prioridad"])),ft.DataCell(ft.Text(x["estado"])),ft.DataCell(ft.Row([ft.IconButton(ft.Icons.PLAY_ARROW,tooltip="Llamar",on_click=lambda _,qid=x["id"]:change(qid,"en_consulta")),ft.IconButton(ft.Icons.CHECK,tooltip="Completar",on_click=lambda _,qid=x["id"]:change(qid,"completado"))]))]))
        holder.controls=[ft.Row([ft.DataTable(columns=[ft.DataColumn(ft.Text(c,weight=ft.FontWeight.BOLD)) for c in ["Turno","Paciente","Médico","Prioridad","Estado","Acciones"]],rows=rows)],scroll=ft.ScrollMode.ALWAYS)]; page.update()
    def change(qid,state): db.update_queue(qid,state); snack(page,"Turno actualizado."); load()
    load()
    return ft.View("/admin/cola",[ft.Container(padding=24,content=ft.Column([page_title("Cola en tiempo real","Control manual de turnos."),holder]))],appbar=app_bar(page,"Cola de espera","admin",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def patients_view(page):
    search=ft.TextField(label="Buscar",prefix_icon=ft.Icons.SEARCH,expand=True); holder=ft.Column()
    def load(_=None):
        d=db.list_patients(search.value or ""); holder.controls=[table(["ID","Nombre","Correo","Teléfono","Nacimiento","Sangre","Alergias"],[[x["id"],x["nombre"],x["correo"],x["telefono"],x["fecha_nac"],x["tipo_sangre"],x["alergias"]] for x in d])]; page.update()
    load()
    return ft.View("/admin/pacientes",[ft.Container(padding=24,content=ft.Column([page_title("Directorio de pacientes","Información de contacto y perfil médico."),ft.ResponsiveRow([ft.Container(search,col={"xs":12,"md":10}),ft.Container(ft.FilledButton("Buscar",icon=ft.Icons.SEARCH,on_click=load),col={"xs":12,"md":2})]),holder]))],appbar=app_bar(page,"Pacientes","admin",HOME,True),scroll=ft.ScrollMode.ALWAYS)

def notifications_view(page):
    holder=ft.Column()
    def load():
        d=db.get_notifications(); rows=[]
        for x in d:
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(x["paciente"] or "—")),ft.DataCell(ft.Text(x["tipo"] or "—")),ft.DataCell(ft.Text(x["canal"] or "—")),ft.DataCell(ft.Text("Enviado" if x["enviado"] else "Pendiente")),ft.DataCell(ft.Text(x["enviado_en"] or "—")),ft.DataCell(ft.IconButton(ft.Icons.SEND,disabled=bool(x["enviado"]),on_click=lambda _,nid=x["id"]:send(nid)))]))
        holder.controls=[ft.Row([ft.DataTable(columns=[ft.DataColumn(ft.Text(c,weight=ft.FontWeight.BOLD)) for c in ["Paciente","Tipo","Canal","Estado","Fecha envío","Acción"]],rows=rows)],scroll=ft.ScrollMode.ALWAYS)]; page.update()
    def send(nid): db.mark_notification_sent(nid); snack(page,"Notificación marcada como enviada."); load()
    load()
    return ft.View("/admin/notificaciones",[ft.Container(padding=24,content=ft.Column([page_title("Notificaciones","Seguimiento de recordatorios."),holder]))],appbar=app_bar(page,"Notificaciones","admin",HOME,True),scroll=ft.ScrollMode.ALWAYS)