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
    search = ft.TextField(label="Buscar paciente", prefix_icon=ft.Icons.SEARCH, expand=True)
    holder = ft.Column()

    def close_dialog(dialog):
        dialog.open = False
        page.update()

    def patient_form(patient_id=None):
        current = db.get_patient(patient_id) if patient_id else None
        nombre = ft.TextField(label="Nombre", value=current["nombre"] if current else "")
        apellidos = ft.TextField(label="Apellidos", value=current["apellidos"] if current else "")
        correo = ft.TextField(label="Correo", value=current["correo"] if current else "")
        telefono = ft.TextField(label="Teléfono", value=current["telefono"] if current else "")
        fecha_nac = ft.TextField(label="Fecha de nacimiento (AAAA-MM-DD)", value=current["fecha_nac"] if current else "")
        sangre = ft.TextField(label="Tipo de sangre", value=current["tipo_sangre"] if current else "")
        alergias = ft.TextField(label="Alergias", value=current["alergias"] if current else "")
        password = ft.TextField(label="Contraseña inicial", password=True, can_reveal_password=True,
                                visible=patient_id is None)

        def save(_):
            if not nombre.value or not apellidos.value or not correo.value:
                snack(page, "Nombre, apellidos y correo son obligatorios.", True); return
            data = {
                "nombre": nombre.value, "apellidos": apellidos.value, "correo": correo.value,
                "telefono": telefono.value or "", "fecha_nac": fecha_nac.value or "",
                "tipo_sangre": sangre.value or "", "alergias": alergias.value or "",
                "contrasena": password.value or "",
            }
            ok, message = (db.update_patient(patient_id, data) if patient_id
                           else db.create_patient(data))
            snack(page, message, not ok)
            if ok:
                close_dialog(dialog)
                load()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar paciente" if patient_id else "Nuevo paciente"),
            content=ft.Container(width=520, content=ft.Column([
                nombre, apellidos, correo, telefono, fecha_nac, sangre, alergias, password
            ], tight=True, scroll=ft.ScrollMode.AUTO)),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_dialog(dialog)),
                ft.FilledButton("Guardar", icon=ft.Icons.SAVE, on_click=save),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def confirm_delete(patient_id, patient_name):
        def delete(_):
            ok, message = db.delete_patient(patient_id)
            snack(page, message, not ok)
            close_dialog(dialog)
            if ok: load()
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Desactivar paciente"),
            content=ft.Text(f"¿Deseas desactivar a {patient_name}? Su expediente no se eliminará."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_dialog(dialog)),
                ft.FilledButton("Desactivar", icon=ft.Icons.PERSON_OFF, on_click=delete),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def load(_=None):
        data = db.list_patients(search.value or "")
        rows = []
        for patient in data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(patient["id"]))),
                ft.DataCell(ft.Text(patient["nombre"])),
                ft.DataCell(ft.Text(patient["correo"])),
                ft.DataCell(ft.Text(patient["telefono"] or "—")),
                ft.DataCell(ft.Text(patient["fecha_nac"] or "—")),
                ft.DataCell(ft.Text(patient["tipo_sangre"] or "—")),
                ft.DataCell(ft.Text(patient["alergias"] or "—")),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar",
                                  on_click=lambda _, pid=patient["id"]: patient_form(pid)),
                    ft.IconButton(ft.Icons.PERSON_OFF, tooltip="Desactivar",
                                  on_click=lambda _, pid=patient["id"], name=patient["nombre"]:
                                      confirm_delete(pid, name)),
                ])),
            ]))
        data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD))
                     for c in ["ID","Nombre","Correo","Teléfono","Nacimiento","Sangre","Alergias","Acciones"]],
            rows=rows,
        )
        holder.controls = [ft.Row([data_table], scroll=ft.ScrollMode.AUTO)]
        page.update()

    load()
    toolbar = ft.ResponsiveRow([
        ft.Container(search, col={"xs":12,"md":8}),
        ft.Container(ft.FilledButton("Buscar", icon=ft.Icons.SEARCH, on_click=load), col={"xs":6,"md":2}),
        ft.Container(ft.FilledButton("Nuevo", icon=ft.Icons.PERSON_ADD,
                                     on_click=lambda _: patient_form()), col={"xs":6,"md":2}),
    ])
    return ft.View("/admin/pacientes",[
        ft.Container(expand=True,padding=24,content=ft.Column([
            page_title("CRUD de pacientes","Crea, consulta, actualiza y desactiva pacientes."),
            toolbar, holder
        ],scroll=ft.ScrollMode.AUTO))
    ],appbar=app_bar(page,"Pacientes","admin",HOME,True),scroll=ft.ScrollMode.AUTO)

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