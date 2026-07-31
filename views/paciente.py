from __future__ import annotations

from datetime import date, timedelta
import flet as ft

import database as db
from components.ui import app_bar, dashboard_card, page_title, snack, table

HOME = "/paciente"


def _user(page: ft.Page) -> dict:
    return page.session.get("user") or {}


def _scroll_content(controls: list[ft.Control]) -> ft.Container:
    return ft.Container(
        expand=True,
        padding=24,
        content=ft.Column(
            controls=controls,
            spacing=18,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )


def dashboard(page: ft.Page) -> ft.View:
    user = _user(page)
    cards = [
        dashboard_card(page, ft.Icons.CALENDAR_MONTH, "Agendar cita",
                       "Programa una consulta médica.", "/paciente/agendar", ft.Colors.BLUE),
        dashboard_card(page, ft.Icons.EVENT_NOTE, "Mis citas",
                       "Consulta próximas citas e historial.", "/paciente/citas", ft.Colors.GREEN),
        dashboard_card(page, ft.Icons.FOLDER_SHARED, "Expediente",
                       "Consulta diagnósticos y recetas.", "/paciente/expediente", ft.Colors.ORANGE),
        dashboard_card(page, ft.Icons.VIDEO_CALL, "Telemedicina",
                       "Entra a tu consulta virtual.", "/paciente/telemedicina", ft.Colors.RED),
        dashboard_card(page, ft.Icons.HOURGLASS_TOP, "Cola virtual",
                       "Consulta tu turno de atención.", "/paciente/cola", ft.Colors.PURPLE),
        dashboard_card(page, ft.Icons.FAVORITE, "Signos vitales",
                       "Registra y consulta tus signos.", "/paciente/signos", ft.Colors.PINK),
    ]

    return ft.View(
        route=HOME,
        controls=[
            _scroll_content([
                page_title(
                    f"Bienvenido/a, {user.get('nombre', 'Paciente')} 👋",
                    "¿Qué deseas hacer hoy?",
                ),
                ft.ResponsiveRow(cards, spacing=16, run_spacing=16),
            ])
        ],
        appbar=app_bar(page, "Clínica-Digital · Portal Paciente",
                       "paciente", HOME),
    )


def appointment_view(page: ft.Page) -> ft.View:
    """Construye el formulario según la política central de agenda."""
    user = _user(page)
    doctors = db.list_doctors()

    doctor = ft.Dropdown(
        label="Médico",
        options=[
            ft.dropdown.Option(
                key=str(item["id"]),
                text=(
                    f'{item["nombre"]} · {item["especialidad"]} · '
                    f'máx. {item["max_citas_dia"]} citas/día'
                ),
            )
            for item in doctors
        ],
        value=str(doctors[0]["id"]) if doctors else None,
    )

    modality = ft.Dropdown(
        label="Modalidad",
        options=[
            ft.dropdown.Option(key="presencial", text="Presencial"),
            ft.dropdown.Option(key="telemedicina", text="Telemedicina"),
        ],
        value="presencial",
    )

    appointment_date = ft.TextField(
        label="Fecha (AAAA-MM-DD)",
        value=str(date.today() + timedelta(days=1)),
        prefix_icon=ft.Icons.DATE_RANGE,
    )

    hour = ft.Dropdown(
        label="Hora",
        options=[
            ft.dropdown.Option(key=value, text=value)
            for value in db.appointment_hours()
        ],
        value="09:00",
    )

    reason = ft.TextField(
        label="Motivo de consulta",
        multiline=True,
        min_lines=3,
        max_lines=5,
    )

    def reserve(_: ft.ControlEvent) -> None:
        try:
            if not doctor.value:
                raise ValueError("Selecciona un médico.")
            if not appointment_date.value:
                raise ValueError("Escribe una fecha.")

            selected_date = date.fromisoformat(appointment_date.value)
            if selected_date < date.today():
                raise ValueError("La fecha no puede estar en el pasado.")

            if not reason.value or not reason.value.strip():
                raise ValueError("Escribe el motivo de consulta.")

            ok, message = db.reserve_appointment(
                user["id"],
                int(doctor.value),
                appointment_date.value,
                hour.value or "09:00",
                modality.value or "presencial",
                reason.value,
            )
            snack(page, message, not ok)

            if ok:
                page.go("/paciente/citas")
        except (TypeError, ValueError) as error:
            snack(page, str(error) or "Revisa los datos.", True)

    form = ft.Container(
        width=760,
        padding=28,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                page_title(
                    "Agendar nueva cita",
                    "Selecciona médico, fecha, horario y modalidad.",
                ),
                ft.Container(
                    padding=12,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE),
                        ft.Text(db.appointment_policy_message(), expand=True),
                    ]),
                ),
                doctor,
                modality,
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=appointment_date,
                            col={"xs": 12, "md": 6},
                        ),
                        ft.Container(
                            content=hour,
                            col={"xs": 12, "md": 6},
                        ),
                    ]
                ),
                reason,
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            "Volver",
                            on_click=lambda _: page.go(HOME),
                        ),
                        ft.FilledButton(
                            "Confirmar cita",
                            icon=ft.Icons.CHECK,
                            on_click=reserve,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    wrap=True,
                ),
            ],
            spacing=16,
        ),
    )

    return ft.View(
        route="/paciente/agendar",
        controls=[
            _scroll_content([
                ft.Row(
                    controls=[form],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ])
        ],
        appbar=app_bar(page, "Agendar cita", "paciente", HOME, True),
    )


def appointments_view(page: ft.Page) -> ft.View:
    user = _user(page)
    data = db.get_patient_appointments(user["id"])

    def cancel(appointment_id: int) -> None:
        if db.cancel_appointment(appointment_id, user["id"]):
            snack(page, "Cita cancelada.")
            page.go("/paciente/citas")
        else:
            snack(page, "No se pudo cancelar la cita.", True)

    def check_in(appointment_id: int) -> None:
        """Solicita turno; la capa de datos valida fecha y horario."""
        ok, message, _ = db.check_in_appointment(appointment_id, user["id"])
        snack(page, message, not ok)
        if ok:
            page.go("/paciente/cola")

    rows = []
    for item in data:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(item["fecha"]))),
                    ft.DataCell(ft.Text(str(item["hora"]))),
                    ft.DataCell(ft.Text(str(item["medico"]))),
                    ft.DataCell(ft.Text(str(item["especialidad"]))),
                    ft.DataCell(ft.Text(str(item["modalidad"]).title())),
                    ft.DataCell(
                        ft.Text(str(item["estado"]).replace("_", " ").title())
                    ),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.HOW_TO_REG,
                                tooltip="Hacer check-in",
                                disabled=item["estado"] != "confirmada"
                                or item["modalidad"] != "presencial",
                                on_click=lambda _, appointment_id=item["id"]:
                                    check_in(appointment_id),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CANCEL_OUTLINED,
                                tooltip="Cancelar",
                                disabled=item["estado"] not in (
                                    "confirmada", "en_espera"
                                ),
                                on_click=lambda _, appointment_id=item["id"]:
                                    cancel(appointment_id),
                            ),
                        ])
                    ),
                ]
            )
        )

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(title, weight=ft.FontWeight.BOLD))
            for title in [
                "Fecha", "Hora", "Médico", "Especialidad",
                "Modalidad", "Estado", "Acción",
            ]
        ],
        rows=rows,
    )

    return ft.View(
        route="/paciente/citas",
        controls=[
            _scroll_content([
                page_title("Mis citas", db.appointment_policy_message()),
                ft.Row(
                    controls=[data_table],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ])
        ],
        appbar=app_bar(page, "Mis citas", "paciente", HOME, True),
    )


def record_view(page: ft.Page) -> ft.View:
    user = _user(page)
    records = db.get_patient_record(user["id"])
    prescriptions = db.get_patient_prescriptions(user["id"])

    profile = ft.Container(
        padding=20,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                ft.Text(
                    "Mi perfil médico",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Text(
                    f'{user.get("nombre", "")} {user.get("apellidos", "")}',
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f'Fecha de nacimiento: {user.get("fecha_nac") or "—"}'
                ),
                ft.Text(
                    f'Tipo de sangre: {user.get("tipo_sangre") or "—"}'
                ),
                ft.Text(f'Alergias: {user.get("alergias") or "—"}'),
            ]
        ),
    )

    visits_table = table(
        ["Fecha", "Médico", "Diagnóstico", "Notas"],
        [
            [
                row["fecha_visita"],
                row["medico"],
                row["diagnostico"],
                row["notas"],
            ]
            for row in records
        ],
    )

    prescriptions_table = table(
        ["Fecha", "Medicamento", "Dosis", "Frecuencia", "Duración", "Médico"],
        [
            [
                row["fecha_emision"],
                row["medicamento"],
                row["dosis"],
                row["frecuencia"],
                row["duracion"],
                row["medico"],
            ]
            for row in prescriptions
        ],
    )

    responsive = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=profile,
                col={"xs": 12, "lg": 3},
            ),
            ft.Container(
                col={"xs": 12, "lg": 9},
                content=ft.Column(
                    controls=[
                        page_title(
                            "Expediente clínico",
                            "Historial de visitas, diagnósticos y recetas.",
                        ),
                        ft.Text(
                            "Consultas y diagnósticos",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        visits_table,
                        ft.Divider(),
                        ft.Text(
                            "Recetas",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        prescriptions_table,
                    ],
                    spacing=14,
                ),
            ),
        ],
        spacing=16,
        run_spacing=16,
    )

    return ft.View(
        route="/paciente/expediente",
        controls=[_scroll_content([responsive])],
        appbar=app_bar(
            page, "Expediente clínico", "paciente", HOME, True
        ),
    )


def telemedicine_view(page: ft.Page) -> ft.View:
    message = ft.TextField(
        label="Mensaje para el médico",
        multiline=True,
        min_lines=2,
    )

    def send(_: ft.ControlEvent) -> None:
        if not message.value or not message.value.strip():
            snack(page, "Escribe un mensaje.", True)
            return

        snack(page, "Mensaje enviado en la demostración.")
        message.value = ""
        page.update()

    panel = ft.Container(
        width=850,
        padding=24,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                page_title(
                    "Telemedicina",
                    "Sala virtual de consulta médica.",
                ),
                ft.Container(
                    height=340,
                    bgcolor=ft.Colors.BLACK87,
                    border_radius=14,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.VIDEOCAM,
                                size=70,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                "Área de videollamada",
                                size=22,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                "Esperando al médico",
                                color=ft.Colors.GREEN_300,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.MIC,
                            tooltip="Micrófono",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.VIDEOCAM,
                            tooltip="Cámara",
                        ),
                        ft.FilledButton(
                            "Colgar",
                            icon=ft.Icons.CALL_END,
                            bgcolor=ft.Colors.RED,
                            on_click=lambda _:
                                snack(page, "Llamada finalizada."),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True,
                ),
                message,
                ft.FilledButton(
                    "Enviar mensaje",
                    icon=ft.Icons.SEND,
                    on_click=send,
                ),
            ],
            spacing=16,
        ),
    )

    return ft.View(
        route="/paciente/telemedicina",
        controls=[
            _scroll_content([
                ft.Row(
                    controls=[panel],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ])
        ],
        appbar=app_bar(
            page, "Telemedicina", "paciente", HOME, True
        ),
    )


def queue_view(page: ft.Page) -> ft.View:
    queue = db.get_queue_for_patient(_user(page)["id"])
    controls = [
        page_title(
            "Cola de espera virtual",
            "Consulta tu posición para la atención presencial.",
        )
    ]

    if queue:
        controls.extend([
            ft.Text(
                f'#{queue["turno"]}',
                size=72,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.PURPLE,
            ),
            ft.Text(
                f'Estado: {queue["estado"].replace("_", " ").title()}',
                size=18,
            ),
            ft.ProgressBar(value=0.7),
        ])
    else:
        controls.extend([
            ft.Icon(
                ft.Icons.CHECK_CIRCLE,
                size=72,
                color=ft.Colors.GREEN,
            ),
            ft.Text("No tienes un turno activo.", size=20),
        ])

    panel = ft.Container(
        width=560,
        padding=35,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    return ft.View(
        route="/paciente/cola",
        controls=[
            _scroll_content([
                ft.Row(
                    controls=[panel],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ])
        ],
        appbar=app_bar(page, "Cola virtual", "paciente", HOME, True),
    )


def vitals_view(page: ft.Page) -> ft.View:
    user = _user(page)

    fields = {
        "temperatura": ft.TextField(
            label="Temperatura °C", value="36.6"
        ),
        "sistolica": ft.TextField(
            label="Presión sistólica", value="120"
        ),
        "diastolica": ft.TextField(
            label="Presión diastólica", value="80"
        ),
        "cardiaca": ft.TextField(
            label="Frecuencia cardíaca", value="72"
        ),
        "saturacion": ft.TextField(
            label="Saturación O₂ %", value="98"
        ),
        "peso": ft.TextField(label="Peso kg", value="74"),
        "sintomas": ft.TextField(
            label="Síntomas",
            multiline=True,
            min_lines=3,
        ),
    }

    history_holder = ft.Column(controls=[])

    def load_history() -> None:
        records = db.get_patient_vitals(user["id"])
        history_holder.controls = [
            table(
                [
                    "Fecha", "Temperatura", "Presión",
                    "FC", "O₂", "Peso", "Síntomas",
                ],
                [
                    [
                        row["registrado_en"],
                        row["temperatura"],
                        f'{row["presion_sistol"]}/{row["presion_diast"]}',
                        row["frec_cardiaca"],
                        row["saturacion_o2"],
                        row["peso_kg"],
                        row["sintomas"],
                    ]
                    for row in records
                ],
            )
        ]

    def save(_: ft.ControlEvent) -> None:
        try:
            data = {
                "temperatura": float(fields["temperatura"].value),
                "sistolica": int(fields["sistolica"].value),
                "diastolica": int(fields["diastolica"].value),
                "cardiaca": int(fields["cardiaca"].value),
                "saturacion": float(fields["saturacion"].value),
                "peso": float(fields["peso"].value),
                "sintomas": fields["sintomas"].value or "",
            }

            db.save_vitals(user["id"], data)
            load_history()
            snack(page, "Signos vitales guardados.")
            page.update()
        except (TypeError, ValueError):
            snack(page, "Usa valores numéricos válidos.", True)

    load_history()

    numeric_fields = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=control,
                col={"xs": 12, "md": 6},
            )
            for key, control in fields.items()
            if key != "sintomas"
        ],
        spacing=12,
        run_spacing=12,
    )

    form = ft.Container(
        width=760,
        padding=28,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                page_title(
                    "Registrar signos vitales",
                    "El médico podrá consultar estos datos.",
                ),
                numeric_fields,
                fields["sintomas"],
                ft.FilledButton(
                    "Guardar registro",
                    icon=ft.Icons.SAVE,
                    on_click=save,
                ),
            ],
            spacing=16,
        ),
    )

    return ft.View(
        route="/paciente/signos",
        controls=[
            _scroll_content([
                ft.Row(
                    controls=[form],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(),
                page_title(
                    "Historial de signos vitales",
                    "Consulta tus registros anteriores.",
                ),
                history_holder,
            ])
        ],
        appbar=app_bar(
            page, "Signos vitales", "paciente", HOME, True
        ),
    )
