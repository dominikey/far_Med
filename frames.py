"""
frames_clinica.py
Pantallas de Clínica-Digital — tres perfiles: Paciente, Médico, Recepción/Dirección.
Estructura inspirada en el proyecto Sweet Balance:
  - Hereda de BackgroundFrame para imagen de fondo intercambiable.
  - ttkbootstrap con tema flatly (claro) / superhero (oscuro).
  - Grid layout, 1000×800 px fijos.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sqlite3
from datetime import datetime


# ──────────────────────────────────────────────
# BASE: BackgroundFrame (igual al proyecto original)
# ──────────────────────────────────────────────
class BackgroundFrame(ttk.Frame):
    """Frame base con imagen de fondo dinámica (cambia con el tema)."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.update_background_image()

    def update_background_image(self):
        img = getattr(self.controller, 'background_image', None)
        if img:
            self.bg_label.configure(image=img)
            self.bg_label.image = img

    # Utilitario: panel semi-transparente sobre el fondo
    def _card(self, parent, **kwargs):
        defaults = dict(bootstyle="light", padding=20)
        defaults.update(kwargs)
        return ttk.Frame(parent, **defaults)


# ══════════════════════════════════════════════
#  PANTALLA 0 — Selección de perfil (Index)
# ══════════════════════════════════════════════
class ClinicaIndexFrame(BackgroundFrame):
    """Pantalla de bienvenida con selección de perfil."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Título centrado
        ttk.Label(self, text="Clínica-Digital",
                  font=("Helvetica", 36, "bold"),
                  bootstyle="inverse-primary").place(relx=0.5, rely=0.18, anchor="center")

        ttk.Label(self, text="Tlaquepaque · Sistema de Gestión Médica",
                  font=("Helvetica", 14),
                  bootstyle="secondary").place(relx=0.5, rely=0.26, anchor="center")

        # Tarjetas de perfil
        perfiles = [
            ("🧑‍⚕️", "Paciente",       "ClinicaLoginFrame", "paciente",    "info"),
            ("👨‍💼", "Médico",          "ClinicaLoginFrame", "medico",      "success"),
            ("🗂️", "Recepción /\nDirección", "ClinicaLoginFrame", "admin", "warning"),
        ]

        card_w, card_h = 220, 200
        start_x = 500 - (len(perfiles) * card_w // 2) - 30

        for i, (icon, label, frame, rol, style) in enumerate(perfiles):
            x = start_x + i * (card_w + 30)
            y = 420

            card = ttk.Frame(self, bootstyle=style, padding=10,
                             width=card_w, height=card_h)
            card.place(x=x, y=y, anchor="center")
            card.pack_propagate(False)

            ttk.Label(card, text=icon, font=("Helvetica", 40)).pack(pady=(10, 5))
            ttk.Label(card, text=label, font=("Helvetica", 14, "bold"),
                      justify="center").pack()
            ttk.Button(card, text="Ingresar", bootstyle=f"{style}-outline",
                       command=lambda f=frame, r=rol: (
                           setattr(controller, 'login_rol', r),
                           controller.show_frame(f)
                       )).pack(pady=(10, 5), fill="x")

        # Pie de versión
        ttk.Label(self, text="v1.0  ·  © 2025 Clínica-Digital",
                  font=("Helvetica", 9),
                  bootstyle="secondary").place(relx=0.5, rely=0.95, anchor="center")


# ══════════════════════════════════════════════
#  PANTALLA 1 — Login unificado
# ══════════════════════════════════════════════
class ClinicaLoginFrame(BackgroundFrame):
    """Login único; el rol ya viene pre-seleccionado desde el Index."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.controller = controller

        # Panel central
        panel = ttk.Frame(self, bootstyle="light", padding=40)
        panel.place(relx=0.5, rely=0.5, anchor="center", width=440, height=460)

        ttk.Label(panel, text="Iniciar Sesión",
                  font=("Helvetica", 22, "bold")).pack(pady=(0, 5))
        ttk.Label(panel, text="Clínica-Digital",
                  font=("Helvetica", 11),
                  bootstyle="secondary").pack(pady=(0, 20))

        # Correo
        ttk.Label(panel, text="Correo electrónico",
                  font=("Helvetica", 11)).pack(anchor="w")
        self.correo_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.correo_var,
                  font=("Helvetica", 12), width=34).pack(fill="x", pady=(4, 14))

        # Contraseña
        ttk.Label(panel, text="Contraseña",
                  font=("Helvetica", 11)).pack(anchor="w")
        self.contrasena_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.contrasena_var,
                  show="*", font=("Helvetica", 12), width=34).pack(fill="x", pady=(4, 24))

        ttk.Button(panel, text="Entrar", bootstyle="primary",
                   command=self._login, width=30).pack(pady=(0, 10))

        ttk.Button(panel, text="← Cambiar perfil", bootstyle="secondary-link",
                   command=lambda: controller.show_frame("ClinicaIndexFrame")).pack()

    def _login(self):
        self.controller.login(self.correo_var.get(), self.contrasena_var.get())


# ══════════════════════════════════════════════
#  PANTALLA 2 — PACIENTE: Panel principal
# ══════════════════════════════════════════════
class PacienteMainFrame(BackgroundFrame):
    """Dashboard principal del paciente."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # ── Barra superior ──────────────────────────────
        navbar = ttk.Frame(self, bootstyle="primary", height=60)
        navbar.place(x=0, y=0, relwidth=1)
        navbar.pack_propagate(False)

        ttk.Label(navbar, text="🏥 Clínica-Digital · Portal Paciente",
                  font=("Helvetica", 14, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)

        ttk.Button(navbar, text="Cerrar sesión", bootstyle="light-outline",
                   command=controller.logout).pack(side="right", padx=20, pady=10)

        ttk.Button(navbar, text="☀/🌙", bootstyle="light-outline",
                   command=controller.toggle_theme).pack(side="right", padx=5, pady=10)

        # ── Cuerpo ────────────────────────────────────
        body = ttk.Frame(self)
        body.place(x=0, y=60, relwidth=1, height=740)

        # Tarjetas de navegación rápida
        acciones = [
            ("📅", "Agendar cita",         "PacienteAgendarFrame",   "info"),
            ("📋", "Mis citas",            "PacienteCitasFrame",     "success"),
            ("📁", "Expediente clínico",   "PacienteExpedienteFrame","warning"),
            ("📹", "Telemedicina",         "PacienteTelemedFrame",   "danger"),
            ("⏳", "Cola de espera",        "PacienteColaFrame",      "secondary"),
            ("💓", "Signos vitales",        "PacienteSignosFrame",    "primary"),
        ]

        ttk.Label(body,
                  text=f"Bienvenido/a 👋",
                  font=("Helvetica", 18, "bold")).place(x=40, y=30)
        ttk.Label(body,
                  text="¿Qué deseas hacer hoy?",
                  font=("Helvetica", 12),
                  bootstyle="secondary").place(x=40, y=62)

        cols, rows = 3, 2
        cw, ch = 260, 150
        pad_x, pad_y = 40, 130

        for idx, (icon, titulo, frame, style) in enumerate(acciones):
            col = idx % cols
            row = idx // cols
            x = pad_x + col * (cw + 20)
            y = pad_y + row * (ch + 20)

            card = ttk.Frame(body, bootstyle=style, padding=15,
                             width=cw, height=ch)
            card.place(x=x, y=y)
            card.pack_propagate(False)

            ttk.Label(card, text=icon,  font=("Helvetica", 28)).pack(anchor="w")
            ttk.Label(card, text=titulo, font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(4, 8))
            ttk.Button(card, text="Abrir →", bootstyle=f"{style}-outline",
                       command=lambda f=frame: controller.show_frame(f)).pack(anchor="w")

        # Panel lateral: próxima cita
        side = ttk.Frame(body, bootstyle="light", padding=20, width=220)
        side.place(x=860, y=20, height=700)
        side.pack_propagate(False)

        ttk.Label(side, text="📌 Próxima cita",
                  font=("Helvetica", 12, "bold")).pack(anchor="w")
        ttk.Separator(side).pack(fill="x", pady=8)
        ttk.Label(side, text="Dra. López\nMedicina General",
                  font=("Helvetica", 10)).pack(anchor="w")
        ttk.Label(side, text="Martes 3 Jun · 10:30 am",
                  bootstyle="info", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=6)
        ttk.Button(side, text="Cancelar cita",
                   bootstyle="danger-outline").pack(fill="x", pady=(0, 10))

        ttk.Separator(side).pack(fill="x", pady=8)
        ttk.Label(side, text="🔔 Recordatorio",
                  font=("Helvetica", 10, "bold")).pack(anchor="w")
        ttk.Label(side,
                  text="Te notificaremos\n24 h y 1 h antes.",
                  font=("Helvetica", 9), wraplength=190,
                  bootstyle="secondary").pack(anchor="w", pady=4)


# ══════════════════════════════════════════════
#  PANTALLA 3 — PACIENTE: Agendar cita
# ══════════════════════════════════════════════
class PacienteAgendarFrame(BackgroundFrame):
    """RQ-001 / RQ-006 — Agendamiento interactivo en tiempo real."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._build_navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=30)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=780, height=620)

        ttk.Label(panel, text="📅 Agendar nueva cita",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Selecciona especialidad, médico y horario disponible.",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 16))

        form = ttk.Frame(panel)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        campos = [
            ("Especialidad:", ["Medicina General", "Pediatría", "Cardiología",
                               "Dermatología", "Neurología"]),
            ("Médico:",        ["Dr. Ramírez", "Dra. López", "Dr. Torres"]),
            ("Modalidad:",     ["Presencial", "Telemedicina"]),
        ]
        self.combos = {}
        for row, (lbl, opts) in enumerate(campos):
            ttk.Label(form, text=lbl, font=("Helvetica", 11)).grid(
                row=row, column=0, sticky="w", pady=8, padx=(0, 16))
            cb = ttk.Combobox(form, values=opts, state="readonly",
                              font=("Helvetica", 11), width=30)
            cb.current(0)
            cb.grid(row=row, column=1, sticky="ew", pady=8)
            self.combos[lbl] = cb

        # Calendario (simulado con botones de días)
        ttk.Label(panel, text="Fecha:",
                  font=("Helvetica", 11)).pack(anchor="w", pady=(14, 4))
        cal_frame = ttk.Frame(panel)
        cal_frame.pack(anchor="w")
        days = ["Lun 2", "Mar 3", "Mié 4", "Jue 5", "Vie 6"]
        self.day_var = tk.StringVar(value=days[0])
        for d in days:
            ttk.Radiobutton(cal_frame, text=d, variable=self.day_var,
                            value=d, bootstyle="info-toolbutton").pack(side="left", padx=4)

        # Horarios disponibles
        ttk.Label(panel, text="Horario disponible:",
                  font=("Helvetica", 11)).pack(anchor="w", pady=(14, 4))
        hora_frame = ttk.Frame(panel)
        hora_frame.pack(anchor="w")
        horas = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                 "12:00", "—", "16:00", "16:30", "17:00"]
        self.hora_var = tk.StringVar(value="09:00")
        for h in horas:
            style = "secondary-outline" if h == "—" else "info-outline"
            state = "disabled" if h == "—" else "normal"
            ttk.Button(hora_frame, text=h, bootstyle=style,
                       state=state, width=6,
                       command=lambda x=h: self.hora_var.set(x)).pack(
                           side="left", padx=3)

        ttk.Label(panel, text="🔒 El horario se bloquea mientras confirmas (lógica transaccional).",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(anchor="w", pady=(10, 0))

        # Motivo
        ttk.Label(panel, text="Motivo de consulta:",
                  font=("Helvetica", 11)).pack(anchor="w", pady=(12, 4))
        self.motivo = tk.Text(panel, height=3, font=("Helvetica", 11))
        self.motivo.pack(fill="x")

        btn_row = ttk.Frame(panel)
        btn_row.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_row, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(side="left")
        ttk.Button(btn_row, text="Confirmar cita ✅", bootstyle="success",
                   command=self._confirmar).pack(side="right")

    def _build_navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="primary", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       side="right", padx=20, pady=10)

    def _confirmar(self):
        messagebox.showinfo("Cita confirmada",
                            "✅ Tu cita ha sido agendada correctamente.\n"
                            "Recibirás un recordatorio 24h y 1h antes.")


# ══════════════════════════════════════════════
#  PANTALLA 4 — PACIENTE: Mis citas
# ══════════════════════════════════════════════
class PacienteCitasFrame(BackgroundFrame):
    """Lista de citas del paciente con opción de cancelar."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=30)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=800, height=580)

        ttk.Label(panel, text="📋 Mis citas",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Historial y citas programadas.",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 16))

        # Filtros
        filtros = ttk.Frame(panel)
        filtros.pack(fill="x", pady=(0, 12))
        for lbl in ["Todas", "Próximas", "Pasadas", "Canceladas"]:
            ttk.Button(filtros, text=lbl,
                       bootstyle="info-outline", width=10).pack(side="left", padx=4)

        # Tabla de citas
        cols = ("Fecha", "Hora", "Médico", "Especialidad", "Modalidad", "Estado")
        tree = ttk.Treeview(panel, columns=cols, show="headings",
                            bootstyle="info", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")

        datos = [
            ("03/06/2025", "10:30", "Dra. López",  "Med. General", "Presencial",    "Confirmada"),
            ("28/05/2025", "09:00", "Dr. Ramírez", "Cardiología",  "Telemedicina",  "Completada"),
            ("15/05/2025", "11:00", "Dr. Torres",  "Neurología",   "Presencial",    "Cancelada"),
        ]
        for d in datos:
            tree.insert("", "end", values=d)

        tree.pack(fill="both", expand=True)

        ttk.Button(panel, text="← Volver al inicio", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       anchor="w", pady=(16, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="primary", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 5 — PACIENTE: Expediente clínico
# ══════════════════════════════════════════════
class PacienteExpedienteFrame(BackgroundFrame):
    """RQ-002 — Expediente clínico digitalizado (solo lectura para paciente)."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        # Layout dividido
        left = ttk.Frame(self, bootstyle="light", padding=20)
        left.place(x=20, y=70, width=280, height=700)
        left.pack_propagate(False)

        ttk.Label(left, text="👤 Mi perfil médico",
                  font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Separator(left).pack(fill="x", pady=4)

        info = [
            ("Nombre",        "Juan Pérez García"),
            ("Fecha nac.",    "12/04/1990"),
            ("Tipo sangre",   "O+"),
            ("Alergias",      "Penicilina"),
            ("Enf. crónicas", "Diabetes T2"),
            ("Peso",          "74 kg"),
            ("Talla",         "1.72 m"),
        ]
        for k, v in info:
            ttk.Label(left, text=k + ":", font=("Helvetica", 10, "bold")).pack(
                anchor="w", pady=(6, 0))
            ttk.Label(left, text=v, font=("Helvetica", 10),
                      bootstyle="secondary").pack(anchor="w")

        # Derecha — historial
        right = ttk.Frame(self, bootstyle="light", padding=20)
        right.place(x=316, y=70, width=664, height=700)

        ttk.Label(right, text="📁 Expediente clínico",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(right,
                  text="Historial de visitas, diagnósticos y recetas (cifrado AES-256).",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 14))

        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True)

        # Tab 1: Visitas
        t1 = ttk.Frame(tabs, padding=10)
        tabs.add(t1, text="🗓 Visitas")
        cols = ("Fecha", "Médico", "Diagnóstico", "Notas")
        tv = ttk.Treeview(t1, columns=cols, show="headings", height=10,
                          bootstyle="info")
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=140)
        visitas = [
            ("28/05/2025", "Dr. Ramírez", "HTA controlada",     "Continúa metformina"),
            ("10/04/2025", "Dra. López",  "Diabetes seguimiento","Glucosa: 98 mg/dL"),
            ("01/03/2025", "Dr. Torres",  "Cefalea tensional",   "Paracetamol 500mg"),
        ]
        for v in visitas:
            tv.insert("", "end", values=v)
        tv.pack(fill="both", expand=True)

        # Tab 2: Recetas
        t2 = ttk.Frame(tabs, padding=10)
        tabs.add(t2, text="💊 Recetas")
        cols2 = ("Fecha", "Medicamento", "Dosis", "Médico")
        tv2 = ttk.Treeview(t2, columns=cols2, show="headings", height=10,
                           bootstyle="success")
        for c in cols2:
            tv2.heading(c, text=c)
            tv2.column(c, width=155)
        recetas = [
            ("28/05/2025", "Metformina 850mg",   "1 c/8h", "Dr. Ramírez"),
            ("10/04/2025", "Losartán 50mg",       "1 c/24h","Dra. López"),
        ]
        for r in recetas:
            tv2.insert("", "end", values=r)
        tv2.pack(fill="both", expand=True)

        # Tab 3: Laboratorios
        t3 = ttk.Frame(tabs, padding=10)
        tabs.add(t3, text="🔬 Laboratorios")
        ttk.Label(t3, text="Últimos resultados:",
                  font=("Helvetica", 11, "bold")).pack(anchor="w", pady=6)
        labs = [
            ("Glucosa en ayunas",  "98 mg/dL",   "Normal"),
            ("HbA1c",              "6.8 %",       "Ligeramente elevado"),
            ("Colesterol total",   "185 mg/dL",   "Normal"),
            ("Presión arterial",   "128/82 mmHg", "Normal"),
        ]
        for lbl, val, estado in labs:
            row = ttk.Frame(t3)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=lbl, width=22).pack(side="left")
            ttk.Label(row, text=val, font=("Helvetica", 10, "bold"),
                      width=16).pack(side="left")
            color = "success" if estado == "Normal" else "warning"
            ttk.Label(row, text=estado, bootstyle=color).pack(side="left")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="primary", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 6 — PACIENTE: Telemedicina
# ══════════════════════════════════════════════
class PacienteTelemedFrame(BackgroundFrame):
    """RQ-003 / RQ-008 — Canal de telemedicina móvil nativo."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=30)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=700, height=560)

        ttk.Label(panel, text="📹 Telemedicina",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Videoconsulta cifrada (WebRTC · VP9 · TURN/STUN propio).",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 20))

        # Área de video simulada
        video_area = ttk.Frame(panel, bootstyle="dark", width=620, height=280)
        video_area.pack(fill="x")
        video_area.pack_propagate(False)
        ttk.Label(video_area,
                  text="🎥  Área de videollamada\n\nConectando con el médico…",
                  font=("Helvetica", 14),
                  bootstyle="inverse-dark",
                  justify="center").place(relx=0.5, rely=0.5, anchor="center")

        # Estado de conexión
        status_frame = ttk.Frame(panel)
        status_frame.pack(fill="x", pady=12)
        ttk.Label(status_frame, text="🟢 Conectado · Latencia: 48 ms",
                  bootstyle="success", font=("Helvetica", 10)).pack(side="left")
        ttk.Label(status_frame, text="Reconexión automática activa (Redis TTL 60s)",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(side="right")

        # Controles
        ctrl = ttk.Frame(panel)
        ctrl.pack(pady=10)
        acciones_ctrl = [
            ("🎤 Micrófono",   "success-outline"),
            ("📷 Cámara",      "info-outline"),
            ("🖥 Compartir",   "warning-outline"),
            ("📞 Colgar",      "danger"),
        ]
        for texto, style in acciones_ctrl:
            ttk.Button(ctrl, text=texto, bootstyle=style,
                       width=13).pack(side="left", padx=6)

        ttk.Separator(panel).pack(fill="x", pady=14)
        ttk.Label(panel, text="💬 Chat de la consulta",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        chat = tk.Text(panel, height=3, font=("Helvetica", 10), state="disabled")
        chat.pack(fill="x", pady=6)
        msg_row = ttk.Frame(panel)
        msg_row.pack(fill="x")
        ttk.Entry(msg_row, font=("Helvetica", 10)).pack(side="left", fill="x",
                                                         expand=True, padx=(0, 8))
        ttk.Button(msg_row, text="Enviar", bootstyle="info").pack(side="right")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="primary", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 7 — PACIENTE: Cola de espera virtual
# ══════════════════════════════════════════════
class PacienteColaFrame(BackgroundFrame):
    """RQ-005 — Gestión de cola de espera virtual (WebSockets)."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=40)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=560, height=480)

        ttk.Label(panel, text="⏳ Cola de espera virtual",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Actualización en tiempo real vía WebSockets.",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 20))

        # Turno actual
        ttk.Label(panel, text="Tu turno", font=("Helvetica", 12)).pack()
        ttk.Label(panel, text="# 7",
                  font=("Helvetica", 56, "bold"),
                  bootstyle="info").pack()
        ttk.Label(panel, text="Turno actual en atención: #5",
                  font=("Helvetica", 12),
                  bootstyle="secondary").pack(pady=(4, 16))

        # Barra de progreso
        ttk.Label(panel, text="Progreso de la cola").pack()
        pb = ttk.Progressbar(panel, value=70, bootstyle="info-striped",
                             length=440)
        pb.pack(pady=8)

        ttk.Label(panel, text="⏱ Tiempo estimado de espera: ~10 minutos",
                  font=("Helvetica", 11, "bold"),
                  bootstyle="warning").pack(pady=10)

        ttk.Label(panel,
                  text="Te notificaremos cuando sea tu turno.\n"
                       "No necesitas permanecer en la sala de espera.",
                  justify="center", font=("Helvetica", 10),
                  bootstyle="secondary").pack()

        ttk.Button(panel, text="🔔 Activar notificaciones push",
                   bootstyle="success-outline").pack(pady=(16, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="primary", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 8 — PACIENTE: Signos vitales preconsulta
# ══════════════════════════════════════════════
class PacienteSignosFrame(BackgroundFrame):
    """RQ-007 — Registro de signos vitales y sintomatología preconsulta."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=30)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=620, height=580)

        ttk.Label(panel, text="💓 Signos vitales preconsulta",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Completa antes de tu consulta (≤ 3 s de sync · TLS 1.3).",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 18))

        form = ttk.Frame(panel)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        campos = [
            ("Temperatura (°C):",       "36.6"),
            ("Presión sistólica (mmHg):","120"),
            ("Presión diastólica (mmHg):","80"),
            ("Frec. cardíaca (lpm):",   "72"),
            ("Saturación O₂ (%):",      "98"),
            ("Peso actual (kg):",        "74"),
        ]
        self.vars = {}
        for i, (lbl, default) in enumerate(campos):
            ttk.Label(form, text=lbl, font=("Helvetica", 11)).grid(
                row=i, column=0, sticky="w", pady=8, padx=(0, 16))
            v = tk.StringVar(value=default)
            ttk.Entry(form, textvariable=v, font=("Helvetica", 11),
                      width=14).grid(row=i, column=1, sticky="w", pady=8)
            self.vars[lbl] = v

        ttk.Label(panel, text="Síntomas principales:",
                  font=("Helvetica", 11)).pack(anchor="w", pady=(14, 4))
        self.sintomas = tk.Text(panel, height=3, font=("Helvetica", 11))
        self.sintomas.pack(fill="x")

        btn_row = ttk.Frame(panel)
        btn_row.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_row, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       side="left")
        ttk.Button(btn_row, text="Guardar y enviar al médico ✅",
                   bootstyle="success",
                   command=lambda: messagebox.showinfo(
                       "Registrado",
                       "✅ Signos vitales enviados al expediente.\n"
                       "El médico los verá antes de tu consulta.")
                   ).pack(side="right")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="primary", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-primary").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("PacienteMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 9 — MÉDICO: Panel principal
# ══════════════════════════════════════════════
class MedicoMainFrame(BackgroundFrame):
    """Dashboard principal del médico."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Navbar
        nb = ttk.Frame(self, bootstyle="success", height=60)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Portal Médico",
                  font=("Helvetica", 14, "bold"),
                  bootstyle="inverse-success").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="Cerrar sesión", bootstyle="light-outline",
                   command=controller.logout).pack(side="right", padx=20, pady=10)
        ttk.Button(nb, text="☀/🌙", bootstyle="light-outline",
                   command=controller.toggle_theme).pack(side="right", padx=5, pady=10)

        body = ttk.Frame(self)
        body.place(x=0, y=60, relwidth=1, height=740)

        ttk.Label(body, text="Bienvenido/a, Dr./Dra. 👨‍⚕️",
                  font=("Helvetica", 18, "bold")).place(x=30, y=24)
        ttk.Label(body, text=f"{datetime.now().strftime('%A %d %B %Y')}",
                  font=("Helvetica", 11),
                  bootstyle="secondary").place(x=30, y=58)

        acciones = [
            ("📅", "Agenda de hoy",           "MedicoAgendaFrame",       "success"),
            ("📁", "Expedientes",              "MedicoExpedientesFrame",  "info"),
            ("📹", "Telemedicina",             "MedicoTelemedicFrame",    "warning"),
            ("📝", "Emitir receta",            "MedicoRecetaFrame",       "primary"),
            ("💓", "Signos vitales recibidos", "MedicoSignosFrame",       "danger"),
        ]

        cw, ch = 280, 140
        pad_x, pad_y = 30, 110

        for idx, (icon, titulo, frame, style) in enumerate(acciones):
            col = idx % 3
            row = idx // 3
            x = pad_x + col * (cw + 24)
            y = pad_y + row * (ch + 18)
            card = ttk.Frame(body, bootstyle=style, padding=14,
                             width=cw, height=ch)
            card.place(x=x, y=y)
            card.pack_propagate(False)
            ttk.Label(card, text=icon,  font=("Helvetica", 26)).pack(anchor="w")
            ttk.Label(card, text=titulo, font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(2, 6))
            ttk.Button(card, text="Abrir →", bootstyle=f"{style}-outline",
                       command=lambda f=frame: controller.show_frame(f)).pack(anchor="w")

        # Panel lateral: paciente actual
        side = ttk.Frame(body, bootstyle="light", padding=18, width=240)
        side.place(x=890, y=14, height=700)
        side.pack_propagate(False)

        ttk.Label(side, text="👤 Paciente en turno",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        ttk.Separator(side).pack(fill="x", pady=6)
        ttk.Label(side, text="Juan Pérez García\n35 años · O+",
                  font=("Helvetica", 10)).pack(anchor="w")
        ttk.Label(side, text="Motivo: revisión diabetes",
                  font=("Helvetica", 9),
                  bootstyle="secondary").pack(anchor="w", pady=4)
        ttk.Button(side, text="Ver expediente",
                   bootstyle="info-outline").pack(fill="x", pady=4)
        ttk.Button(side, text="Iniciar consulta",
                   bootstyle="success").pack(fill="x")

        ttk.Separator(side).pack(fill="x", pady=10)
        ttk.Label(side, text="📊 Resumen del día",
                  font=("Helvetica", 10, "bold")).pack(anchor="w")
        stats = [("Citas agendadas", "12"), ("Atendidas", "5"),
                 ("No-shows", "1"), ("Telemedicina", "3")]
        for k, v in stats:
            row_f = ttk.Frame(side)
            row_f.pack(fill="x", pady=2)
            ttk.Label(row_f, text=k,
                      font=("Helvetica", 9),
                      bootstyle="secondary").pack(side="left")
            ttk.Label(row_f, text=v,
                      font=("Helvetica", 10, "bold")).pack(side="right")


# ══════════════════════════════════════════════
#  PANTALLA 10 — MÉDICO: Agenda del día
# ══════════════════════════════════════════════
class MedicoAgendaFrame(BackgroundFrame):
    """Vista de citas del día para el médico."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=28)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=860, height=600)

        ttk.Label(panel, text="📅 Agenda de hoy",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text=f"Lunes 2 de junio, 2025 · Dr. Ramírez",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 16))

        cols = ("Hora", "Paciente", "Motivo", "Modalidad", "Estado", "Acción")
        tree = ttk.Treeview(panel, columns=cols, show="headings",
                            bootstyle="success", height=14)
        widths = [70, 160, 180, 110, 100, 110]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        citas = [
            ("09:00", "María Gómez",    "Revisión HTA",        "Presencial",   "Completada",   "—"),
            ("09:30", "Luis Hernández", "Dolor de cabeza",     "Presencial",   "En espera",    "Iniciar"),
            ("10:00", "Ana Torres",     "Control glucosa",     "Telemedicina", "En espera",    "Videollamar"),
            ("10:30", "Juan Pérez",     "Diabetes seguimiento","Presencial",   "En turno",     "Ver exp."),
            ("11:00", "—",              "—",                   "—",            "No-show",      "—"),
            ("11:30", "Rosa Medina",    "Cefalea",             "Presencial",   "Confirmada",   "—"),
        ]
        tags_color = {
            "Completada": "success", "En espera": "warning",
            "No-show": "danger",     "En turno": "info",
        }
        for c in citas:
            tag = tags_color.get(c[4], "")
            tree.insert("", "end", values=c, tags=(tag,))

        tree.pack(fill="both", expand=True)
        ttk.Button(panel, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       anchor="w", pady=(14, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="success", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Médico",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-success").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 11 — MÉDICO: Expedientes
# ══════════════════════════════════════════════
class MedicoExpedientesFrame(BackgroundFrame):
    """RQ-002 / RQ-009 — Expedientes con bitácora de acceso."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=24)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=900, height=620)

        ttk.Label(panel, text="📁 Gestión de expedientes",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Cada acceso queda en bitácora (HMAC-SHA256 · retención 5 años).",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 12))

        # Buscador
        search_row = ttk.Frame(panel)
        search_row.pack(fill="x", pady=(0, 12))
        ttk.Label(search_row, text="🔍 Buscar paciente:").pack(side="left", padx=(0, 8))
        ttk.Entry(search_row, width=30, font=("Helvetica", 11)).pack(side="left")
        ttk.Button(search_row, text="Buscar", bootstyle="info").pack(side="left", padx=8)

        cols = ("ID", "Nombre", "Edad", "Última visita", "Diagnóstico principal")
        tv = ttk.Treeview(panel, columns=cols, show="headings",
                          bootstyle="info", height=10)
        for c, w in zip(cols, [60, 180, 50, 120, 260]):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="center")

        pacientes = [
            ("P001", "Juan Pérez García",    35, "28/05/2025", "Diabetes T2"),
            ("P002", "Ana Torres Ruiz",      48, "22/05/2025", "Hipertensión arterial"),
            ("P003", "Carlos Vega López",    62, "15/05/2025", "EPOC"),
            ("P004", "María Gómez Soto",     29, "01/06/2025", "Cefalea tensional"),
        ]
        for p in pacientes:
            tv.insert("", "end", values=p)
        tv.pack(fill="both", expand=True)

        btns = ttk.Frame(panel)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="👁 Ver expediente", bootstyle="info").pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="✏️ Agregar nota", bootstyle="warning").pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="📋 Ver bitácora", bootstyle="secondary").pack(side="left")
        ttk.Button(btns, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(side="right")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="success", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Médico",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-success").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 12 — MÉDICO: Telemedicina
# ══════════════════════════════════════════════
class MedicoTelemedicFrame(BackgroundFrame):
    """RQ-003 — Vista de telemedicina para el médico."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        # Layout dos columnas
        left = ttk.Frame(self, bootstyle="light", padding=20)
        left.place(x=14, y=70, width=340, height=710)
        left.pack_propagate(False)

        ttk.Label(left, text="📋 Datos del paciente",
                  font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Separator(left).pack(fill="x", pady=4)
        datos = [("Paciente", "Ana Torres"), ("Edad", "48 años"),
                 ("Motivo", "Control HTA"), ("Presión", "130/85 mmHg"),
                 ("Glucosa", "104 mg/dL"),  ("Frec. card.", "76 lpm")]
        for k, v in datos:
            ttk.Label(left, text=k + ":", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(6, 0))
            ttk.Label(left, text=v, bootstyle="secondary",
                      font=("Helvetica", 10)).pack(anchor="w")

        ttk.Separator(left).pack(fill="x", pady=10)
        ttk.Label(left, text="📝 Notas de consulta:",
                  font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.notas = tk.Text(left, height=8, font=("Helvetica", 10))
        self.notas.pack(fill="x", pady=4)
        ttk.Button(left, text="💾 Guardar notas",
                   bootstyle="success").pack(fill="x", pady=4)
        ttk.Button(left, text="💊 Emitir receta",
                   bootstyle="warning").pack(fill="x")

        # Derecha: video
        right = ttk.Frame(self, bootstyle="light", padding=16)
        right.place(x=370, y=70, width=616, height=710)
        right.pack_propagate(False)

        ttk.Label(right, text="📹 Videoconsulta en curso",
                  font=("Helvetica", 15, "bold")).pack(anchor="w", pady=(0, 8))

        video = ttk.Frame(right, bootstyle="dark", width=580, height=340)
        video.pack()
        video.pack_propagate(False)
        ttk.Label(video, text="🎥  Video del paciente\n\n Ana Torres",
                  font=("Helvetica", 14),
                  bootstyle="inverse-dark",
                  justify="center").place(relx=0.5, rely=0.5, anchor="center")

        status = ttk.Frame(right)
        status.pack(fill="x", pady=8)
        ttk.Label(status, text="🟢 Activa · 48 ms · 1080p",
                  bootstyle="success", font=("Helvetica", 10)).pack(side="left")
        ttk.Label(status, text="RQ-008: reconexión automática activa",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(side="right")

        ctrl = ttk.Frame(right)
        ctrl.pack(pady=8)
        for txt, sty in [("🎤", "success-outline"), ("📷", "info-outline"),
                          ("📞 Finalizar", "danger")]:
            ttk.Button(ctrl, text=txt, bootstyle=sty, width=12).pack(
                side="left", padx=6)

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="success", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Médico",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-success").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 13 — MÉDICO: Emitir receta
# ══════════════════════════════════════════════
class MedicoRecetaFrame(BackgroundFrame):
    """Emisión de receta médica digital."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=30)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=680, height=580)

        ttk.Label(panel, text="📝 Emitir receta médica",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel, text="La receta queda vinculada al expediente del paciente.",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 16))

        form = ttk.Frame(panel)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Paciente:", font=("Helvetica", 11)).grid(
            row=0, column=0, sticky="w", pady=8, padx=(0, 14))
        ttk.Combobox(form, values=["Juan Pérez García", "Ana Torres",
                                    "María Gómez"], state="readonly",
                     font=("Helvetica", 11), width=32).grid(
            row=0, column=1, sticky="ew", pady=8)

        ttk.Label(form, text="Medicamento:", font=("Helvetica", 11)).grid(
            row=1, column=0, sticky="w", pady=8, padx=(0, 14))
        ttk.Entry(form, font=("Helvetica", 11), width=32).grid(
            row=1, column=1, sticky="ew", pady=8)

        ttk.Label(form, text="Dosis:", font=("Helvetica", 11)).grid(
            row=2, column=0, sticky="w", pady=8, padx=(0, 14))
        ttk.Entry(form, font=("Helvetica", 11), width=20).grid(
            row=2, column=1, sticky="w", pady=8)

        ttk.Label(form, text="Frecuencia:", font=("Helvetica", 11)).grid(
            row=3, column=0, sticky="w", pady=8, padx=(0, 14))
        freq_cb = ttk.Combobox(form,
                                values=["Cada 8 horas", "Cada 12 horas",
                                        "Cada 24 horas", "Al despertar"],
                                state="readonly", font=("Helvetica", 11), width=20)
        freq_cb.current(0)
        freq_cb.grid(row=3, column=1, sticky="w", pady=8)

        ttk.Label(form, text="Duración:", font=("Helvetica", 11)).grid(
            row=4, column=0, sticky="w", pady=8, padx=(0, 14))
        ttk.Entry(form, font=("Helvetica", 11), width=20).grid(
            row=4, column=1, sticky="w", pady=8)

        ttk.Label(panel, text="Indicaciones especiales:",
                  font=("Helvetica", 11)).pack(anchor="w", pady=(10, 4))
        self.indicaciones = tk.Text(panel, height=3, font=("Helvetica", 11))
        self.indicaciones.pack(fill="x")

        btn_row = ttk.Frame(panel)
        btn_row.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_row, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       side="left")
        ttk.Button(btn_row, text="📤 Emitir receta",
                   bootstyle="warning",
                   command=lambda: messagebox.showinfo(
                       "Receta emitida",
                       "✅ Receta guardada en el expediente del paciente.")
                   ).pack(side="right")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="success", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Médico",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-success").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 14 — MÉDICO: Signos vitales recibidos
# ══════════════════════════════════════════════
class MedicoSignosFrame(BackgroundFrame):
    """RQ-007 — Médico ve signos vitales enviados por el paciente."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=28)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=780, height=540)

        ttk.Label(panel, text="💓 Signos vitales del paciente",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Datos enviados antes de la consulta vía API REST (TLS 1.3).",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 16))

        # Paciente selector
        sel = ttk.Frame(panel)
        sel.pack(fill="x", pady=(0, 14))
        ttk.Label(sel, text="Paciente:").pack(side="left", padx=(0, 8))
        ttk.Combobox(sel, values=["Juan Pérez García", "Ana Torres"],
                     state="readonly", width=26).pack(side="left")
        ttk.Button(sel, text="Cargar", bootstyle="info").pack(side="left", padx=8)

        # Tarjetas de signos
        signos = [
            ("🌡", "Temperatura",   "36.6 °C",    "Normal",      "success"),
            ("❤️", "Frec. cardíaca", "72 lpm",     "Normal",      "success"),
            ("🩺", "P. sistólica",  "128 mmHg",   "Límite alto", "warning"),
            ("🩺", "P. diastólica", "82 mmHg",    "Normal",      "success"),
            ("💧", "Saturación O₂", "98 %",       "Normal",      "success"),
            ("⚖️", "Peso",          "74 kg",      "—",           "info"),
        ]

        grid = ttk.Frame(panel)
        grid.pack(fill="x")
        for idx, (icon, nombre, valor, estado, style) in enumerate(signos):
            col = idx % 3
            row = idx // 3
            card = ttk.Frame(grid, bootstyle=style, padding=14, width=220, height=100)
            card.grid(row=row, column=col, padx=8, pady=8)
            card.pack_propagate(False)
            ttk.Label(card, text=f"{icon} {nombre}",
                      font=("Helvetica", 10, "bold")).pack(anchor="w")
            ttk.Label(card, text=valor,
                      font=("Helvetica", 16, "bold")).pack(anchor="w")
            ttk.Label(card, text=estado,
                      bootstyle=style, font=("Helvetica", 9)).pack(anchor="w")

        ttk.Label(panel, text="Síntomas reportados: Ligero dolor de cabeza al despertar.",
                  font=("Helvetica", 10),
                  bootstyle="secondary").pack(anchor="w", pady=(10, 0))

        ttk.Button(panel, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       anchor="w", pady=(16, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="success", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Médico",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-success").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("MedicoMainFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 15 — RECEPCIÓN/DIRECCIÓN: Panel principal
# ══════════════════════════════════════════════
class AdminMainClinicaFrame(BackgroundFrame):
    """Dashboard principal de Recepción y Dirección."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        nb = ttk.Frame(self, bootstyle="warning", height=60)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Recepción / Dirección",
                  font=("Helvetica", 14, "bold"),
                  bootstyle="inverse-warning").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="Cerrar sesión", bootstyle="light-outline",
                   command=controller.logout).pack(side="right", padx=20, pady=10)
        ttk.Button(nb, text="☀/🌙", bootstyle="light-outline",
                   command=controller.toggle_theme).pack(side="right", padx=5, pady=10)

        body = ttk.Frame(self)
        body.place(x=0, y=60, relwidth=1, height=740)

        ttk.Label(body, text="Panel de Administración",
                  font=("Helvetica", 18, "bold")).place(x=30, y=24)

        acciones = [
            ("📅", "Gestión de citas",        "AdminCitasFrame",      "warning"),
            ("📊", "Dashboard KPIs",          "AdminKPIsFrame",        "danger"),
            ("👥", "Pacientes",               "AdminPacientesFrame",   "info"),
            ("⏳", "Cola en tiempo real",      "AdminColaRealFrame",    "success"),
            ("🔔", "Notificaciones / no-shows","AdminNotifFrame",       "secondary"),
        ]

        cw, ch = 270, 140
        pad_x, pad_y = 30, 100

        for idx, (icon, titulo, frame, style) in enumerate(acciones):
            col = idx % 3
            row = idx // 3
            x = pad_x + col * (cw + 22)
            y = pad_y + row * (ch + 18)
            card = ttk.Frame(body, bootstyle=style, padding=14,
                             width=cw, height=ch)
            card.place(x=x, y=y)
            card.pack_propagate(False)
            ttk.Label(card, text=icon, font=("Helvetica", 26)).pack(anchor="w")
            ttk.Label(card, text=titulo,
                      font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(2, 6))
            ttk.Button(card, text="Abrir →", bootstyle=f"{style}-outline",
                       command=lambda f=frame: controller.show_frame(f)).pack(anchor="w")

        # Panel lateral KPIs rápidos
        side = ttk.Frame(body, bootstyle="light", padding=18, width=240)
        side.place(x=890, y=14, height=700)
        side.pack_propagate(False)
        ttk.Label(side, text="📈 KPIs del día",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        ttk.Separator(side).pack(fill="x", pady=6)
        kpis = [
            ("Citas agendadas",  "34"),
            ("Atendidas",        "21"),
            ("No-shows",         "2"),
            ("Telemedicina",     "8"),
            ("Ocup. consultorio","78 %"),
            ("T. espera prom.",  "12 min"),
        ]
        for k, v in kpis:
            r = ttk.Frame(side)
            r.pack(fill="x", pady=3)
            ttk.Label(r, text=k,
                      font=("Helvetica", 9),
                      bootstyle="secondary").pack(side="left")
            ttk.Label(r, text=v,
                      font=("Helvetica", 10, "bold")).pack(side="right")


# ══════════════════════════════════════════════
#  PANTALLA 16 — ADMIN: Gestión de citas
# ══════════════════════════════════════════════
class AdminCitasFrame(BackgroundFrame):
    """Recepción: creación, modificación y cancelación de citas."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=24)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=900, height=620)

        ttk.Label(panel, text="📅 Gestión de citas",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Reserva, modifica o cancela citas (bloqueo transaccional en BD).",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 12))

        toolbar = ttk.Frame(panel)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="➕ Nueva cita",
                   bootstyle="warning").pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="✏️ Modificar",
                   bootstyle="info").pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="❌ Cancelar",
                   bootstyle="danger-outline").pack(side="left")

        cols = ("ID", "Paciente",       "Médico",      "Especialidad",
                "Fecha",      "Hora",  "Modalidad",    "Estado")
        tv = ttk.Treeview(panel, columns=cols, show="headings",
                          bootstyle="warning", height=14)
        ws = [50, 160, 130, 130, 90, 60, 110, 100]
        for c, w in zip(cols, ws):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="center")

        citas = [
            ("C001", "Juan Pérez",   "Dr. Ramírez", "Med. General",
             "03/06", "10:30", "Presencial",   "Confirmada"),
            ("C002", "Ana Torres",   "Dra. López",  "Cardiología",
             "03/06", "11:00", "Telemedicina", "Confirmada"),
            ("C003", "Luis Hdz.",    "Dr. Torres",  "Neurología",
             "03/06", "11:30", "Presencial",   "En espera"),
            ("C004", "Rosa Medina",  "Dr. Ramírez", "Med. General",
             "03/06", "12:00", "Presencial",   "No-show"),
        ]
        for c in citas:
            tv.insert("", "end", values=c)
        tv.pack(fill="both", expand=True)

        ttk.Button(panel, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       anchor="w", pady=(12, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="warning", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Recepción",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-warning").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 17 — ADMIN: Dashboard KPIs (RQ-010)
# ══════════════════════════════════════════════
class AdminKPIsFrame(BackgroundFrame):
    """RQ-010 — Dashboard de indicadores operativos (DSS)."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=24)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=940, height=650)

        header = ttk.Frame(panel)
        header.pack(fill="x")
        ttk.Label(header, text="📊 Dashboard de KPIs operativos",
                  font=("Helvetica", 18, "bold")).pack(side="left")
        ttk.Label(header,
                  text="Datos con antigüedad máx. 5 min · polling 60 s",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(
                      side="right", pady=6)

        # Filtros de período
        filt = ttk.Frame(panel)
        filt.pack(fill="x", pady=(8, 16))
        ttk.Label(filt, text="Período:").pack(side="left", padx=(0, 8))
        for p in ["Hoy", "Esta semana", "Este mes"]:
            ttk.Button(filt, text=p,
                       bootstyle="danger-outline", width=12).pack(side="left", padx=4)

        # Tarjetas KPI principales
        kpis = [
            ("📋", "Citas totales",       "34",    "+8 vs ayer",  "danger"),
            ("✅", "Pacientes atendidos", "21",    "62 % de ocup.","success"),
            ("🚫", "No-shows",            "2",     "Obj. ≤ 10 %", "warning"),
            ("📹", "Telemedicina",         "8",     "38 % del día", "info"),
            ("⏱", "T. espera promedio",   "12 min","Obj. ≤ 15 min","success"),
            ("💰", "Ingresos del día",    "$14,200","Por consulta", "primary"),
        ]

        kpi_grid = ttk.Frame(panel)
        kpi_grid.pack(fill="x", pady=(0, 16))
        for idx, (icon, nombre, valor, sub, style) in enumerate(kpis):
            col = idx % 3
            row = idx // 3
            card = ttk.Frame(kpi_grid, bootstyle=style, padding=16,
                             width=280, height=100)
            card.grid(row=row, column=col, padx=8, pady=8)
            card.pack_propagate(False)
            top = ttk.Frame(card)
            top.pack(fill="x")
            ttk.Label(top, text=f"{icon} {nombre}",
                      font=("Helvetica", 10, "bold")).pack(side="left")
            ttk.Label(card, text=valor,
                      font=("Helvetica", 22, "bold")).pack(anchor="w")
            ttk.Label(card, text=sub,
                      bootstyle=style, font=("Helvetica", 9)).pack(anchor="w")

        # Barra de saturación
        ttk.Label(panel, text="Ocupación de consultorios",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        ttk.Progressbar(panel, value=78, bootstyle="danger-striped",
                         length=880).pack(fill="x", pady=6)
        ttk.Label(panel, text="78 % ocupación · Sala A: 90 % · Sala B: 65 %",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(anchor="w")

        ttk.Button(panel, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       anchor="w", pady=(14, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="warning", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Dirección",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-warning").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 18 — ADMIN: Cola en tiempo real
# ══════════════════════════════════════════════
class AdminColaRealFrame(BackgroundFrame):
    """RQ-005 — Vista de cola de espera para recepción."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=24)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=860, height=590)

        header = ttk.Frame(panel)
        header.pack(fill="x")
        ttk.Label(header, text="⏳ Cola de espera en tiempo real",
                  font=("Helvetica", 18, "bold")).pack(side="left")
        ttk.Label(header, text="WebSockets · FIFO con priorización",
                  bootstyle="secondary", font=("Helvetica", 9)).pack(side="right")

        cols = ("Turno", "Paciente",     "Cita",    "Espera",
                "Modalidad",  "Prioridad", "Estado")
        tv = ttk.Treeview(panel, columns=cols, show="headings",
                          bootstyle="success", height=14)
        ws = [60, 160, 60, 80, 110, 90, 110]
        for c, w in zip(cols, ws):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="center")

        cola = [
            ("#5",  "María Gómez",   "09:00", "5 min",  "Presencial",   "Normal",   "En consulta"),
            ("#6",  "Luis Hdz.",     "09:30", "12 min", "Presencial",   "Normal",   "En espera"),
            ("#7",  "Ana Torres",    "10:00", "18 min", "Telemedicina", "Normal",   "En espera"),
            ("#8",  "Rosa Medina",   "10:30", "—",      "Presencial",   "Adulto mayor","En espera"),
            ("#9",  "Juan Pérez",    "11:00", "—",      "Presencial",   "Normal",   "Agendado"),
        ]
        for c in cola:
            tv.insert("", "end", values=c)
        tv.pack(fill="both", expand=True)

        ctrl = ttk.Frame(panel)
        ctrl.pack(fill="x", pady=(12, 0))
        ttk.Button(ctrl, text="▶ Llamar siguiente",
                   bootstyle="success").pack(side="left", padx=(0, 8))
        ttk.Button(ctrl, text="⏸ Pausar turno",
                   bootstyle="warning-outline").pack(side="left", padx=(0, 8))
        ttk.Button(ctrl, text="🔔 Notificar paciente",
                   bootstyle="info-outline").pack(side="left")
        ttk.Button(ctrl, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="warning", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Recepción",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-warning").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 19 — ADMIN: Pacientes CRUD
# ══════════════════════════════════════════════
class AdminPacientesFrame(BackgroundFrame):
    """CRUD de pacientes para recepción."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=24)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=900, height=610)

        ttk.Label(panel, text="👥 Gestión de pacientes",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Alta, búsqueda y actualización de datos.",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 12))

        toolbar = ttk.Frame(panel)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Entry(toolbar, width=28, font=("Helvetica", 11)).pack(
            side="left", padx=(0, 8))
        ttk.Button(toolbar, text="🔍 Buscar",
                   bootstyle="info").pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="➕ Nuevo paciente",
                   bootstyle="warning").pack(side="left")

        cols = ("ID", "Nombre",             "CURP",          "F. Nac.",
                "Teléfono",    "Correo",         "Últ. visita")
        tv = ttk.Treeview(panel, columns=cols, show="headings",
                          bootstyle="info", height=13)
        ws = [50, 180, 140, 80, 100, 160, 90]
        for c, w in zip(cols, ws):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="center")

        pacs = [
            ("P001", "Juan Pérez García",  "PEGJ900412XXX","12/04/1990",
             "3311223344","jpg@mail.com",  "28/05/2025"),
            ("P002", "Ana Torres Ruiz",    "TORA760815XXX","15/08/1976",
             "3398877665","atr@mail.com",  "22/05/2025"),
            ("P003", "Carlos Vega López",  "VELC630201XXX","01/02/1963",
             "3312345678","cvl@mail.com",  "15/05/2025"),
        ]
        for p in pacs:
            tv.insert("", "end", values=p)
        tv.pack(fill="both", expand=True)

        btns = ttk.Frame(panel)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="✏️ Editar",  bootstyle="warning").pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="🗑 Eliminar", bootstyle="danger-outline").pack(side="left")
        ttk.Button(btns, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right")

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="warning", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Recepción",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-warning").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  PANTALLA 20 — ADMIN: Notificaciones y no-shows (RQ-004)
# ══════════════════════════════════════════════
class AdminNotifFrame(BackgroundFrame):
    """RQ-004 — Gestión de recordatorios y seguimiento de no-shows."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._navbar(controller)

        panel = ttk.Frame(self, bootstyle="light", padding=24)
        panel.place(relx=0.5, rely=0.52, anchor="center", width=860, height=590)

        ttk.Label(panel, text="🔔 Notificaciones y no-shows",
                  font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(panel,
                  text="Recordatorios automáticos 24 h y 1 h antes de la cita.",
                  bootstyle="secondary").pack(anchor="w", pady=(0, 12))

        # KPI no-shows
        kpi_row = ttk.Frame(panel)
        kpi_row.pack(fill="x", pady=(0, 14))
        for label, val, style in [
            ("No-shows hoy", "2", "danger"),
            ("Tasa mes",     "8.2 %", "warning"),
            ("Obj. ≤ 10 %",  "✅ Cumplido", "success"),
        ]:
            c = ttk.Frame(kpi_row, bootstyle=style, padding=14, width=200, height=80)
            c.pack(side="left", padx=8)
            c.pack_propagate(False)
            ttk.Label(c, text=label, font=("Helvetica", 10, "bold")).pack(anchor="w")
            ttk.Label(c, text=val, font=("Helvetica", 16, "bold")).pack(anchor="w")

        tabs = ttk.Notebook(panel)
        tabs.pack(fill="both", expand=True)

        # Tab 1: Recordatorios pendientes
        t1 = ttk.Frame(tabs, padding=10)
        tabs.add(t1, text="📤 Recordatorios pendientes")
        cols = ("Paciente", "Cita", "Hora cita", "Canal", "Estado")
        tv1 = ttk.Treeview(t1, columns=cols, show="headings",
                           bootstyle="warning", height=8)
        for c in cols:
            tv1.heading(c, text=c)
            tv1.column(c, width=160, anchor="center")
        recordatorios = [
            ("Ana Torres",  "03/06", "10:00", "SMS + App", "24h enviado ✅"),
            ("Luis Hdz.",   "03/06", "09:30", "App",       "1h pendiente ⏳"),
            ("Rosa Medina", "03/06", "12:00", "SMS",       "Enviando… 📤"),
        ]
        for r in recordatorios:
            tv1.insert("", "end", values=r)
        tv1.pack(fill="both", expand=True)
        ttk.Button(t1, text="📤 Reenviar seleccionado",
                   bootstyle="warning").pack(anchor="w", pady=8)

        # Tab 2: No-shows del mes
        t2 = ttk.Frame(tabs, padding=10)
        tabs.add(t2, text="🚫 No-shows del mes")
        cols2 = ("Fecha", "Paciente", "Médico", "Especialidad", "Acción tomada")
        tv2 = ttk.Treeview(t2, columns=cols2, show="headings",
                           bootstyle="danger", height=8)
        for c in cols2:
            tv2.heading(c, text=c)
            tv2.column(c, width=160, anchor="center")
        noshows = [
            ("01/06", "Pedro Ruiz",  "Dr. Torres",  "Neurología",   "Llamada realizada"),
            ("28/05", "Laura Díaz",  "Dr. Ramírez", "Med. General", "Reagendada"),
            ("25/05", "Jorge Salinas","Dra. López",  "Cardiología",  "Sin contacto"),
        ]
        for n in noshows:
            tv2.insert("", "end", values=n)
        tv2.pack(fill="both", expand=True)

        ttk.Button(panel, text="← Volver", bootstyle="secondary-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       anchor="w", pady=(12, 0))

    def _navbar(self, controller):
        nb = ttk.Frame(self, bootstyle="warning", height=55)
        nb.place(x=0, y=0, relwidth=1)
        nb.pack_propagate(False)
        ttk.Label(nb, text="🏥 Clínica-Digital · Recepción",
                  font=("Helvetica", 13, "bold"),
                  bootstyle="inverse-warning").pack(side="left", padx=20, pady=10)
        ttk.Button(nb, text="← Inicio", bootstyle="light-outline",
                   command=lambda: controller.show_frame("AdminMainClinicaFrame")).pack(
                       side="right", padx=20, pady=10)


# ══════════════════════════════════════════════
#  EXPORTACIÓN: lista de todos los frames
# ══════════════════════════════════════════════
ALL_FRAMES = [
    ClinicaIndexFrame,
    ClinicaLoginFrame,
    # Paciente
    PacienteMainFrame,
    PacienteAgendarFrame,
    PacienteCitasFrame,
    PacienteExpedienteFrame,
    PacienteTelemedFrame,
    PacienteColaFrame,
    PacienteSignosFrame,
    # Médico
    MedicoMainFrame,
    MedicoAgendaFrame,
    MedicoExpedientesFrame,
    MedicoTelemedicFrame,
    MedicoRecetaFrame,
    MedicoSignosFrame,
    # Admin / Recepción
    AdminMainClinicaFrame,
    AdminCitasFrame,
    AdminKPIsFrame,
    AdminColaRealFrame,
    AdminPacientesFrame,
    AdminNotifFrame,
]