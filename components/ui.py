from __future__ import annotations

from typing import Any

import flet as ft


ROLE_COLORS = {
    "paciente": ft.Colors.BLUE,
    "medico": ft.Colors.GREEN,
    "admin": ft.Colors.ORANGE,
}


def snack(
    page: ft.Page,
    message: str,
    error: bool = False,
) -> None:
    """Muestra un mensaje inferior en la aplicación."""

    page.snack_bar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        show_close_icon=True,
    )

    page.snack_bar.open = True
    page.update()


def page_title(
    title: str,
    subtitle: str = "",
) -> ft.Control:
    """Genera el título y subtítulo de una pantalla."""

    controls: list[ft.Control] = [
        ft.Text(
            title,
            size=30,
            weight=ft.FontWeight.BOLD,
        )
    ]

    if subtitle:
        controls.append(
            ft.Text(
                subtitle,
                size=15,
                color=ft.Colors.GREY_600,
            )
        )

    return ft.Column(
        controls=controls,
        spacing=4,
    )


def app_bar(
    page: ft.Page,
    title: str,
    role: str,
    home_route: str,
    show_back: bool = False,
) -> ft.AppBar:
    """Crea la barra superior de las vistas."""

    role_color = ROLE_COLORS.get(role, ft.Colors.BLUE)

    leading = None

    if show_back:
        leading = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=ft.Colors.WHITE,
            tooltip="Volver",
            on_click=lambda _: page.go(home_route),
        )

    def logout(_: ft.ControlEvent) -> None:
        page.session.clear()
        page.go("/")

    return ft.AppBar(
        leading=leading,
        title=ft.Text(
            title,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
        ),
        bgcolor=role_color,
        center_title=False,
        actions=[
            ft.IconButton(
                icon=ft.Icons.HOME,
                icon_color=ft.Colors.WHITE,
                tooltip="Inicio",
                on_click=lambda _: page.go(home_route),
            ),
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                icon_color=ft.Colors.WHITE,
                tooltip="Cerrar sesión",
                on_click=logout,
            ),
        ],
    )


def dashboard_card(
    page: ft.Page,
    icon: str,
    title: str,
    description: str,
    route: str,
    color: str,
) -> ft.Container:
    """Crea una tarjeta del menú principal."""

    return ft.Container(
        col={
            "xs": 12,
            "sm": 6,
            "lg": 4,
        },
        padding=22,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column(
            controls=[
                ft.Container(
                    width=58,
                    height=58,
                    border_radius=15,
                    bgcolor=color,
                    alignment=ft.alignment.center,
                    content=ft.Icon(
                        icon,
                        size=31,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Text(
                    title,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    description,
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.FilledButton(
                    text="Abrir",
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda _: page.go(route),
                ),
            ],
            spacing=12,
        ),
    )


def stat_card(
    title: str,
    value: Any,
    icon: str,
    color: str,
) -> ft.Container:
    """Crea una tarjeta para mostrar estadísticas."""

    return ft.Container(
        col={
            "xs": 12,
            "sm": 6,
            "lg": 4,
        },
        padding=20,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Row(
            controls=[
                ft.Container(
                    width=52,
                    height=52,
                    border_radius=14,
                    bgcolor=color,
                    alignment=ft.alignment.center,
                    content=ft.Icon(
                        icon,
                        color=ft.Colors.WHITE,
                        size=28,
                    ),
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            str(value),
                            size=27,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            title,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=1,
                ),
            ],
            spacing=15,
        ),
    )


def table(
    columns: list[str],
    rows: list[list[Any]],
) -> ft.Control:
    """Crea una tabla reutilizable con desplazamiento horizontal."""

    data_columns = [
        ft.DataColumn(
            ft.Text(
                column,
                weight=ft.FontWeight.BOLD,
            )
        )
        for column in columns
    ]

    data_rows = []

    for row in rows:
        cells = [
            ft.DataCell(
                ft.Text(
                    "—" if value is None else str(value)
                )
            )
            for value in row
        ]

        data_rows.append(
            ft.DataRow(cells=cells)
        )

    if not data_rows:
        return ft.Container(
            padding=30,
            alignment=ft.alignment.center,
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.INBOX_OUTLINED,
                        size=45,
                        color=ft.Colors.GREY_500,
                    ),
                    ft.Text(
                        "No hay información disponible.",
                        color=ft.Colors.GREY_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    data_table = ft.DataTable(
        columns=data_columns,
        rows=data_rows,
        column_spacing=30,
        heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        border=ft.border.all(
            1,
            ft.Colors.OUTLINE_VARIANT,
        ),
        border_radius=12,
    )

    return ft.Row(
        controls=[data_table],
        scroll=ft.ScrollMode.ALWAYS,
    )