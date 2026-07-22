from __future__ import annotations

import flet as ft

import database as db
from components.ui import (
    app_bar,
    dashboard_card,
    page_title,
    snack,
    stat_card,
    table,
)

HOME = "/medico"


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
    agenda = db.get_doctor_agenda(user["medico_id"])

    cards = [
        dashboard_card(
            page, ft.Icons.CALENDAR_TODAY, "Agenda de hoy",
            "Pacientes y consultas del día.",
            "/medico/agenda", ft.Colors.GREEN,
        ),
        dashboard_card(
            page, ft.Icons.FOLDER_SHARED, "Expedientes",
            "Busca pacientes y revisa sus datos.",
            "/medico/expedientes", ft.Colors.BLUE,
        ),
        dashboard_card(
            page, ft.Icons.VIDEO_CALL, "Telemedicina",
            "Sala virtual para consulta.",
            "/medico/telemedicina", ft.Colors.ORANGE,
        ),
        dashboard_card(
            page, ft.Icons.MEDICATION, "Emitir receta",
            "Registra una receta digital.",
            "/medico/receta", ft.Colors.PURPLE,
        ),
        dashboard_card(
            page, ft.Icons.MONITOR_HEART, "Signos vitales",
            "Consulta el historial de pacientes.",
            "/medico/signos", ft.Colors.RED,
        ),
    ]

    return ft.View(
        route=HOME,
        controls=[
            _scroll_content([
                page_title(
                    f'Dr./Dra. {user.get("nombre", "")} '
                    f'{user.get("apellidos", "")}',
                    user.get("especialidad", "Portal médico"),
                ),
                ft.ResponsiveRow(
                    controls=[
                        stat_card(
                            "Citas de hoy",
                            len(agenda),
                            ft.Icons.EVENT,
                            ft.Colors.GREEN,
                        ),
                        stat_card(
                            "En espera",
                            sum(
                                item["estado"] == "en_espera"
                                for item in agenda
                            ),
                            ft.Icons.HOURGLASS_TOP,
                            ft.Colors.ORANGE,
                        ),
                        stat_card(
                            "Telemedicina",
                            sum(
                                item["modalidad"] == "telemedicina"
                                for item in agenda
                            ),
                            ft.Icons.VIDEO_CALL,
                            ft.Colors.BLUE,
                        ),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
                ft.ResponsiveRow(
                    controls=cards,
                    spacing=16,
                    run_spacing=16,
                ),
            ])
        ],
        appbar=app_bar(
            page, "Clínica-Digital · Portal Médico",
            "medico", HOME,
        ),
    )


def agenda_view(page: ft.Page) -> ft.View:
    user = _user(page)
    if not user.get("medico_id"):
        return ft.View(
            route="/medico/agenda",
            controls=[
                _scroll_content([
                    page_title(
                        "Agenda de hoy",
                        "No se encontró el perfil del médico.",
                    )
                ])
            ],
            appbar=app_bar(
                page, "Agenda médica", "medico", HOME, True
            ),
        )

    data = db.get_doctor_agenda(user["medico_id"])

    agenda_table = table(
        ["Hora", "Paciente", "Motivo", "Modalidad", "Estado"],
        [
            [
                row["hora"],
                row["paciente"],
                row["motivo"],
                row["modalidad"],
                row["estado"],
            ]
            for row in data
        ],
    )

    return ft.View(
        route="/medico/agenda",
        controls=[
            _scroll_content([
                page_title(
                    "Agenda de hoy",
                    "Citas asignadas al médico.",
                ),
                agenda_table,
            ])
        ],
        appbar=app_bar(
            page, "Agenda médica", "medico", HOME, True
        ),
    )


def records_view(page: ft.Page) -> ft.View:
    search = ft.TextField(
        label="Buscar paciente",
        prefix_icon=ft.Icons.SEARCH,
    )
    holder = ft.Column(controls=[])

    def load(_: ft.ControlEvent | None = None) -> None:
        patients = db.list_patients(search.value or "")
        holder.controls = [
            table(
                [
                    "ID", "Nombre", "Correo", "Teléfono",
                    "Nacimiento", "Sangre", "Alergias",
                ],
                [
                    [
                        row["id"],
                        row["nombre"],
                        row["correo"],
                        row["telefono"],
                        row["fecha_nac"],
                        row["tipo_sangre"],
                        row["alergias"],
                    ]
                    for row in patients
                ],
            )
        ]
        page.update()

    load()

    toolbar = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=search,
                col={"xs": 12, "md": 9},
            ),
            ft.Container(
                content=ft.FilledButton(
                    "Buscar",
                    icon=ft.Icons.SEARCH,
                    on_click=load,
                ),
                col={"xs": 12, "md": 3},
            ),
        ]
    )

    return ft.View(
        route="/medico/expedientes",
        controls=[
            _scroll_content([
                page_title(
                    "Gestión de expedientes",
                    "Busca pacientes y consulta sus datos.",
                ),
                toolbar,
                holder,
            ])
        ],
        appbar=app_bar(
            page, "Expedientes", "medico", HOME, True
        ),
    )


def telemedicine_view(page: ft.Page) -> ft.View:
    notes = ft.TextField(
        label="Notas de consulta",
        multiline=True,
        min_lines=7,
    )

    def save_notes(_: ft.ControlEvent) -> None:
        if not notes.value or not notes.value.strip():
            snack(page, "Escribe notas de consulta.", True)
            return
        snack(page, "Notas guardadas en la demostración.")

    patient_panel = ft.Container(
        col={"xs": 12, "lg": 4},
        padding=20,
        border_radius=16,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                ft.Text(
                    "Datos del paciente",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Selecciona la cita activa desde la agenda."
                ),
                notes,
                ft.FilledButton(
                    "Guardar notas",
                    icon=ft.Icons.SAVE,
                    on_click=save_notes,
                ),
            ],
            spacing=14,
        ),
    )

    video_panel = ft.Container(
        col={"xs": 12, "lg": 8},
        padding=20,
        border_radius=16,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                page_title(
                    "Videoconsulta",
                    "Sala virtual del médico.",
                ),
                ft.Container(
                    height=380,
                    bgcolor=ft.Colors.BLACK87,
                    border_radius=14,
                    alignment=ft.alignment.center,
                    content=ft.Icon(
                        ft.Icons.VIDEOCAM,
                        size=80,
                        color=ft.Colors.WHITE,
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
                            "Finalizar",
                            icon=ft.Icons.CALL_END,
                            bgcolor=ft.Colors.RED,
                            on_click=lambda _:
                                snack(page, "Consulta finalizada."),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True,
                ),
            ],
            spacing=16,
        ),
    )

    return ft.View(
        route="/medico/telemedicina",
        controls=[
            _scroll_content([
                ft.ResponsiveRow(
                    controls=[patient_panel, video_panel],
                    spacing=16,
                    run_spacing=16,
                )
            ])
        ],
        appbar=app_bar(
            page, "Telemedicina médica", "medico", HOME, True
        ),
    )


def prescription_view(page: ft.Page) -> ft.View:
    user = _user(page)
    patients = db.list_patients()

    patient = ft.Dropdown(
        label="Paciente",
        options=[
            ft.dropdown.Option(
                key=str(row["id"]),
                text=row["nombre"],
            )
            for row in patients
        ],
    )

    medication = ft.TextField(label="Medicamento")
    dose = ft.TextField(label="Dosis")
    frequency = ft.TextField(label="Frecuencia")
    duration = ft.TextField(label="Duración")
    instructions = ft.TextField(
        label="Indicaciones",
        multiline=True,
        min_lines=3,
    )

    def save(_: ft.ControlEvent) -> None:
        if not user.get("medico_id"):
            snack(page, "No se encontró el perfil del médico.", True)
            return

        if not patient.value:
            snack(page, "Selecciona un paciente.", True)
            return

        if not medication.value or not medication.value.strip():
            snack(page, "Escribe el medicamento.", True)
            return

        db.create_prescription(
            user["medico_id"],
            int(patient.value),
            medication.value,
            dose.value or "",
            frequency.value or "",
            duration.value or "",
            instructions.value or "",
        )

        snack(page, "Receta emitida correctamente.")

        patient.value = None
        for field in [
            medication, dose, frequency, duration, instructions
        ]:
            field.value = ""

        page.update()

    form = ft.Container(
        width=760,
        padding=28,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                page_title(
                    "Emitir receta digital",
                    "La receta quedará vinculada al paciente.",
                ),
                patient,
                medication,
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=dose,
                            col={"xs": 12, "md": 4},
                        ),
                        ft.Container(
                            content=frequency,
                            col={"xs": 12, "md": 4},
                        ),
                        ft.Container(
                            content=duration,
                            col={"xs": 12, "md": 4},
                        ),
                    ],
                    spacing=12,
                    run_spacing=12,
                ),
                instructions,
                ft.FilledButton(
                    "Emitir receta",
                    icon=ft.Icons.MEDICATION,
                    on_click=save,
                ),
            ],
            spacing=16,
        ),
    )

    return ft.View(
        route="/medico/receta",
        controls=[
            _scroll_content([
                ft.Row(
                    controls=[form],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ])
        ],
        appbar=app_bar(
            page, "Nueva receta", "medico", HOME, True
        ),
    )


def vitals_view(page: ft.Page) -> ft.View:
    patients = db.list_patients()

    patient = ft.Dropdown(
        label="Paciente",
        options=[
            ft.dropdown.Option(
                key=str(row["id"]),
                text=row["nombre"],
            )
            for row in patients
        ],
        value=str(patients[0]["id"]) if patients else None,
    )

    holder = ft.Column(controls=[])

    def load(_: ft.ControlEvent | None = None) -> None:
        if not patient.value:
            holder.controls = [
                ft.Text("No hay pacientes disponibles.")
            ]
        else:
            data = db.get_patient_vitals(int(patient.value))
            holder.controls = [
                table(
                    [
                        "Fecha", "Temperatura", "Presión",
                        "FC", "O₂", "Peso", "Síntomas",
                    ],
                    [
                        [
                            row["registrado_en"],
                            row["temperatura"],
                            f'{row["presion_sistol"]}/'
                            f'{row["presion_diast"]}',
                            row["frec_cardiaca"],
                            row["saturacion_o2"],
                            row["peso_kg"],
                            row["sintomas"],
                        ]
                        for row in data
                    ],
                )
            ]

        page.update()

    load()

    toolbar = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=patient,
                col={"xs": 12, "md": 9},
            ),
            ft.Container(
                content=ft.FilledButton(
                    "Consultar",
                    icon=ft.Icons.SEARCH,
                    on_click=load,
                ),
                col={"xs": 12, "md": 3},
            ),
        ]
    )

    return ft.View(
        route="/medico/signos",
        controls=[
            _scroll_content([
                page_title(
                    "Historial de signos vitales",
                    "Selecciona un paciente para consultar sus registros.",
                ),
                toolbar,
                holder,
            ])
        ],
        appbar=app_bar(
            page, "Signos vitales", "medico", HOME, True
        ),
    )