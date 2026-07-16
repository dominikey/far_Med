from __future__ import annotations
import flet as ft
from database import authenticate
from components.ui import snack


def index_view(page: ft.Page) -> ft.View:
    def choose(role: str):
        page.session.set("login_role", role)
        page.go("/login")
    cards = []
    data = [
        ("paciente", "Paciente", ft.Icons.PERSON, ft.Colors.BLUE_700),
        ("medico", "Médico", ft.Icons.MEDICAL_SERVICES, ft.Colors.GREEN_700),
        ("admin", "Recepción / Dirección", ft.Icons.ADMIN_PANEL_SETTINGS, ft.Colors.AMBER_800),
    ]
    for role, label, icon, color in data:
        cards.append(ft.Container(
            col={"xs": 12, "md": 4}, padding=24, border_radius=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Column([ft.Icon(icon, size=58, color=color), ft.Text(label, size=20, weight=ft.FontWeight.BOLD),
                               ft.FilledButton("Ingresar", on_click=lambda _, r=role: choose(r))], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ))
    return ft.View("/", [ft.Container(
        expand=True, padding=40,
        content=ft.Column([
            ft.Icon(ft.Icons.LOCAL_HOSPITAL, size=80, color=ft.Colors.BLUE_700),
            ft.Text("Clínica-Digital", size=40, weight=ft.FontWeight.BOLD),
            ft.Text("Tlaquepaque · Sistema de Gestión Médica", size=16, color=ft.Colors.GREY_600),
            ft.Container(height=20), ft.ResponsiveRow(cards, spacing=20),
            ft.Text("v2.0 · Aplicación Flet", color=ft.Colors.GREY_500),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
    )], bgcolor=ft.Colors.SURFACE)


def login_view(page: ft.Page) -> ft.View:
    role = page.session.get("login_role") or "paciente"
    email = ft.TextField(label="Correo electrónico", prefix_icon=ft.Icons.EMAIL, autofocus=True)
    password = ft.TextField(label="Contraseña", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True)

    def login(_):
        if not email.value or not password.value:
            snack(page, "Completa correo y contraseña.", True); return
        user = authenticate(email.value, password.value, role)
        if not user:
            snack(page, "Credenciales incorrectas o el perfil no coincide.", True); return
        page.session.set("user", user)
        page.go({"paciente": "/paciente", "medico": "/medico", "admin": "/admin"}[user["rol"]])

    return ft.View("/login", [ft.Container(expand=True, alignment=ft.alignment.center, content=ft.Container(
        width=440, padding=36, border_radius=20, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([
            ft.Icon(ft.Icons.LOCAL_HOSPITAL, size=55, color=ft.Colors.BLUE_700),
            ft.Text("Iniciar sesión", size=28, weight=ft.FontWeight.BOLD),
            ft.Text(f"Perfil seleccionado: {role.title()}", color=ft.Colors.GREY_600),
            email, password,
            ft.FilledButton("Entrar", icon=ft.Icons.LOGIN, width=340, on_click=login),
            ft.TextButton("← Cambiar perfil", on_click=lambda _: page.go("/")),
            ft.Divider(),
            ft.Text("Prueba: juan@mail.com / paciente1", size=12),
            ft.Text("Médico: cramires@clinica.mx / medico123", size=12),
            ft.Text("Admin: admin@clinica.mx / admin123", size=12),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=14),
    ))])