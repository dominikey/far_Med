import flet as ft
from database import authenticate


class LoginView(ft.View):
    """Clase pública de compatibilidad para el inicio de sesión."""

    def __init__(self, page: ft.Page):
        super().__init__(
            route="/login",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
        )

        # Un guion bajo indica acceso protegido para posibles subclases.
        self._page = page

        self._correo = ft.TextField(
            label="Correo electrónico",
            width=350,
            prefix_icon=ft.Icons.EMAIL,
        )

        # Dos guiones bajos aplican name mangling: atributo privado.
        self.__password = ft.TextField(
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

                        self._correo,

                        self.__password,

                        ft.ElevatedButton(
                            "Ingresar",
                            icon=ft.Icons.LOGIN,
                            width=350,
                            height=50,
                            on_click=self._login,
                        ),

                    ],
                ),
            )
        ]

    def _login(self, _event):
        """Método protegido que delega la verificación segura."""

        correo = self._correo.value.strip()
        password = self.__password.value

        if correo == "" or password == "":

            self._page.snack_bar = ft.SnackBar(
                ft.Text("Debes llenar todos los campos")
            )
            self._page.snack_bar.open = True
            self._page.update()
            return

        usuario = authenticate(correo, password)

        if usuario is None:

            self._page.snack_bar = ft.SnackBar(
                ft.Text("Correo o contraseña incorrectos")
            )
            self._page.snack_bar.open = True
            self._page.update()
            return

        self._page.session.set("user", usuario)

        rol = usuario["rol"]

        if rol == "paciente":
            self._page.go("/paciente")

        elif rol == "medico":
            self._page.go("/medico")

        elif rol == "admin":
            self._page.go("/admin")
