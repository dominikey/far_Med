import flet as ft


class HomeView(ft.View):

    def __init__(self, page: ft.Page):

        super().__init__(
            route="/home",
            bgcolor=ft.Colors.GREY_100,
        )

        self.page = page

        self.controls = [
            self.appbar(),
            self.body()
        ]

    # ------------------------
    # Barra superior
    # ------------------------

    def appbar(self):

        return ft.AppBar(
            bgcolor=ft.Colors.BLUE_700,
            title=ft.Text(
                "🏥 Clínica Digital",
                color="white",
                size=22,
                weight=ft.FontWeight.BOLD,
            ),
            center_title=False,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE,
                    icon_color="white",
                    tooltip="Cambiar tema",
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color="white",
                    tooltip="Cerrar sesión",
                    on_click=lambda e: self.page.go("/")
                )
            ]
        )

    # ------------------------
    # Cuerpo principal
    # ------------------------

    def body(self):

        return ft.Container(
            expand=True,
            padding=30,
            content=ft.Column(
                controls=[

                    ft.Text(
                        "Bienvenido 👋",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.Text(
                        "¿Qué deseas hacer hoy?",
                        color=ft.Colors.GREY_700,
                        size=16,
                    ),

                    ft.Divider(),

                    self.grid_cards(),

                ],
                expand=True,
            )
        )

    # ------------------------
    # Tarjetas
    # ------------------------

    def grid_cards(self):

        return ft.ResponsiveRow(
            controls=[

                self.card(
                    "📅",
                    "Agendar cita",
                    ft.Colors.BLUE,
                    "/agendar"
                ),

                self.card(
                    "📋",
                    "Mis citas",
                    ft.Colors.GREEN,
                    "/citas"
                ),

                self.card(
                    "📁",
                    "Expediente",
                    ft.Colors.ORANGE,
                    "/expediente"
                ),

                self.card(
                    "📹",
                    "Telemedicina",
                    ft.Colors.RED,
                    "/telemedicina"
                ),

                self.card(
                    "⏳",
                    "Cola de espera",
                    ft.Colors.PURPLE,
                    "/cola"
                ),

                self.card(
                    "💓",
                    "Signos vitales",
                    ft.Colors.CYAN,
                    "/signos"
                ),

            ]
        )

    # ------------------------
    # Tarjeta individual
    # ------------------------

    def card(self, emoji, titulo, color, ruta):

        return ft.Container(

            col={"sm": 12, "md": 6, "xl": 4},

            margin=10,

            border_radius=18,

            bgcolor="white",

            shadow=ft.BoxShadow(
                blur_radius=15,
                spread_radius=1,
                color=ft.Colors.BLACK12,
            ),

            padding=20,

            content=ft.Column(

                horizontal_alignment=ft.CrossAxisAlignment.CENTER,

                controls=[

                    ft.Text(
                        emoji,
                        size=42,
                    ),

                    ft.Text(
                        titulo,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),

                    ft.Container(height=10),

                    ft.ElevatedButton(
                        "Abrir",
                        icon=ft.Icons.ARROW_FORWARD,
                        bgcolor=color,
                        color="white",
                        width=180,
                        on_click=lambda e: self.page.go(ruta)
                    )

                ]
            )
        )