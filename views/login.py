import flet as ft
import sqlite3

DB_NAME = "clinica_digital.db"


class LoginView(ft.View):

    def __init__(self, page: ft.Page):
        super().__init__(
            route="/login",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
        )

        self.page = page

        self.correo = ft.TextField(
            label="Correo electrónico",
            width=350,
            prefix_icon=ft.Icons.EMAIL,
        )

        self.password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=350,
            prefix_icon=ft.Icons.LOCK,
        )

        self.controls = [
            ft.Container(
                width=420,
                padding=40,
                border_radius=20,
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(
                    blur_radius=15,
                    spread_radius=2,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.LOCAL_HOSPITAL,
                            size=70,
                            color=ft.Colors.BLUE,
                        ),

                        ft.Text(
                            "Clínica Digital",
                            size=30,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Text(
                            "Iniciar Sesión",
                            color=ft.Colors.GREY_700,
                        ),

                        ft.Divider(),

                        self.correo,

                        self.password,

                        ft.ElevatedButton(
                            "Ingresar",
                            icon=ft.Icons.LOGIN,
                            width=350,
                            height=50,
                            on_click=self.login,
                        ),

                    ],
                ),
            )
        ]

    def login(self, e):

        correo = self.correo.value.strip()
        password = self.password.value.strip()

        if correo == "" or password == "":

            self.page.snack_bar = ft.SnackBar(
                ft.Text("Debes llenar todos los campos")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nombre,
                apellidos,
                correo,
                rol
            FROM usuarios
            WHERE correo=?
            AND contrasena=?
            """,
            (correo, password),
        )

        usuario = cursor.fetchone()

        conn.close()

        if usuario is None:

            self.page.snack_bar = ft.SnackBar(
                ft.Text("Correo o contraseña incorrectos")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        self.page.session.set(
            "usuario",
            {
                "id": usuario[0],
                "nombre": usuario[1],
                "apellidos": usuario[2],
                "correo": usuario[3],
                "rol": usuario[4],
            },
        )

        rol = usuario[4]

        if rol == "paciente":
            self.page.go("/paciente")

        elif rol == "medico":
            self.page.go("/medico")

        elif rol == "admin":
            self.page.go("/admin")