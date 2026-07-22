from __future__ import annotations
import flet as ft
from database import authenticate, create_password_reset_code, reset_password
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
            ft.TextButton("¿Olvidaste tu contraseña?", icon=ft.Icons.LOCK_RESET, on_click=lambda _: page.go("/recuperar")),
            ft.TextButton("← Cambiar perfil", on_click=lambda _: page.go("/")),
            ft.Divider(),
            ft.Text("Prueba: juan@mail.com / paciente1", size=12),
            ft.Text("Médico: cramires@clinica.mx / medico123", size=12),
            ft.Text("Admin: admin@clinica.mx / admin123", size=12),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=14),
    ))])


def forgot_password_view(page: ft.Page) -> ft.View:
    email = ft.TextField(label="Correo electrónico", prefix_icon=ft.Icons.EMAIL)
    demo_code = ft.Text("", selectable=True, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)

    def request_code(_):
        if not email.value:
            snack(page, "Escribe tu correo.", True)
            return
        code = create_password_reset_code(email.value)
        snack(page, "Si el correo existe, se generó un código temporal.")
        if code:
            page.session.set("reset_email", email.value.strip())
            demo_code.value = f"Código de prueba: {code} (válido 15 minutos)"
            page.update()

    panel = ft.Container(width=520, padding=32, border_radius=20,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_RESET, size=60, color=ft.Colors.BLUE),
            ft.Text("Recuperar contraseña", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("En producción el código debe enviarse por correo."),
            email,
            ft.FilledButton("Generar código", on_click=request_code),
            demo_code,
            ft.FilledButton("Continuar", on_click=lambda _: page.go("/restablecer")),
            ft.TextButton("Volver", on_click=lambda _: page.go("/login")),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16))
    return ft.View("/recuperar", [ft.Container(expand=True, alignment=ft.alignment.center,
                                                padding=20, content=panel)])


def reset_password_view(page: ft.Page) -> ft.View:
    email = ft.TextField(label="Correo", value=page.session.get("reset_email") or "")
    code = ft.TextField(label="Código de 6 dígitos")
    password = ft.TextField(label="Nueva contraseña", password=True, can_reveal_password=True)
    confirm = ft.TextField(label="Confirmar contraseña", password=True, can_reveal_password=True)

    def save(_):
        if not all([email.value, code.value, password.value, confirm.value]):
            snack(page, "Completa todos los campos.", True); return
        if password.value != confirm.value:
            snack(page, "Las contraseñas no coinciden.", True); return
        ok, message = reset_password(email.value, code.value, password.value)
        snack(page, message, not ok)
        if ok:
            page.go("/login")

    panel = ft.Container(width=520, padding=32, border_radius=20,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Column([
            ft.Text("Restablecer contraseña", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Usa 8 caracteres, mayúscula, minúscula y número."),
            email, code, password, confirm,
            ft.FilledButton("Guardar nueva contraseña", icon=ft.Icons.SAVE, on_click=save),
            ft.TextButton("Volver", on_click=lambda _: page.go("/login")),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14))
    return ft.View("/restablecer", [ft.Container(expand=True, alignment=ft.alignment.center,
                                                   padding=20, content=panel)])