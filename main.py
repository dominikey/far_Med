from __future__ import annotations

import traceback
import flet as ft

import database as db
from views import admin, auth, medico, paciente

PUBLIC_ROUTES = {"/", "/login", "/recuperar", "/restablecer"}
ROLE_HOME = {
    "paciente": "/paciente",
    "medico": "/medico",
    "admin": "/admin",
}


def main(page: ft.Page) -> None:
    db.setup_database()

    page.title = "Clínica-Digital · Flet"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE, use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE, use_material3=True)
    page.padding = 0

    routes = {
        "/": auth.index_view,
        "/login": auth.login_view,
        "/recuperar": auth.forgot_password_view,
        "/restablecer": auth.reset_password_view,

        "/paciente": paciente.dashboard,
        "/paciente/agendar": paciente.appointment_view,
        "/paciente/citas": paciente.appointments_view,
        "/paciente/expediente": paciente.record_view,
        "/paciente/telemedicina": paciente.telemedicine_view,
        "/paciente/cola": paciente.queue_view,
        "/paciente/signos": paciente.vitals_view,

        "/medico": medico.dashboard,
        "/medico/agenda": medico.agenda_view,
        "/medico/expedientes": medico.records_view,
        "/medico/telemedicina": medico.telemedicine_view,
        "/medico/receta": medico.prescription_view,
        "/medico/signos": medico.vitals_view,

        "/admin": admin.dashboard,
        "/admin/citas": admin.appointments_view,
        "/admin/kpis": admin.kpis_view,
        "/admin/cola": admin.queue_view,
        "/admin/pacientes": admin.patients_view,
        "/admin/notificaciones": admin.notifications_view,
    }

    def normalize_route(route: str | None) -> str:
        route = (route or "/").split("?", 1)[0].strip()
        if not route.startswith("/"):
            route = f"/{route}"
        if len(route) > 1:
            route = route.rstrip("/")
        return route

    def error_view(route: str, error: Exception) -> ft.View:
        return ft.View(
            route=route,
            controls=[
                ft.Container(
                    expand=True,
                    padding=30,
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=70, color=ft.Colors.RED),
                            ft.Text("No se pudo abrir esta página", size=28, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Ruta: {route}"),
                            ft.Text(str(error), selectable=True, color=ft.Colors.RED_700),
                            ft.FilledButton(
                                "Volver al inicio",
                                icon=ft.Icons.HOME,
                                on_click=lambda _: page.go(
                                    ROLE_HOME.get((page.session.get("user") or {}).get("rol"), "/")
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                )
            ],
        )

    def route_change(event: ft.RouteChangeEvent) -> None:
        route = normalize_route(event.route)
        print(f"Navegando a: {route}")

        if route == "/logout":
            page.session.clear()
            page.go("/")
            return

        user = page.session.get("user")

        if route not in PUBLIC_ROUTES:
            if not user:
                page.go("/")
                return

            role = user.get("rol")
            allowed_home = ROLE_HOME.get(role)

            if not allowed_home:
                page.session.clear()
                page.go("/")
                return

            # Evita que un paciente abra rutas de médico o administrador.
            if route != allowed_home and not route.startswith(f"{allowed_home}/"):
                page.go(allowed_home)
                return

        builder = routes.get(route)
        if builder is None:
            destination = ROLE_HOME.get((user or {}).get("rol"), "/")
            if route != destination:
                page.go(destination)
            return

        try:
            new_view = builder(page)
            page.views.clear()
            page.views.append(new_view)
        except Exception as error:
            traceback.print_exc()
            page.views.clear()
            page.views.append(error_view(route, error))

        page.update()

    def view_pop(_: ft.ViewPopEvent) -> None:
        user = page.session.get("user") or {}
        page.go(ROLE_HOME.get(user.get("rol"), "/"))

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(normalize_route(page.route))


if __name__ == "__main__":
    ft.app(target=main)