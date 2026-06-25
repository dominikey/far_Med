"""
main_clinica.py
Punto de entrada de Clínica-Digital.
Integra los tres perfiles (Paciente, Médico, Recepción/Dirección)
en una sola ventana con cambio de tema claro/oscuro.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sqlite3

from frames import (
    # Base
    BackgroundFrame,
    # Entrada
    ClinicaIndexFrame, ClinicaLoginFrame,
    # Paciente
    PacienteMainFrame, PacienteAgendarFrame, PacienteCitasFrame,
    PacienteExpedienteFrame, PacienteTelemedFrame, PacienteColaFrame,
    PacienteSignosFrame,
    # Médico
    MedicoMainFrame, MedicoAgendaFrame, MedicoExpedientesFrame,
    MedicoTelemedicFrame, MedicoRecetaFrame, MedicoSignosFrame,
    # Admin / Recepción
    AdminMainClinicaFrame, AdminCitasFrame, AdminKPIsFrame,
    AdminColaRealFrame, AdminPacientesFrame, AdminNotifFrame,
    # Lista completa
    ALL_FRAMES,
)
from database import setup_database


class ClinicaDigitalApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("Clínica-Digital · Tlaquepaque")
        self.geometry("1000x800")
        self.resizable(False, False)

        # Estado de sesión
        self.current_user = None
        self.login_rol    = None          # 'paciente' | 'medico' | 'admin'
        self.theme_name   = "flatly"

        # ── Imágenes de fondo ──────────────────────────
        self.background_images = {}
        self.background_image  = None
        self._load_backgrounds()

        # ── Ícono de la aplicación ────────────────────
        self._load_icon()

        # ── Inicializar base de datos ──────────────────
        setup_database()

        # ── Contenedor principal ──────────────────────
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # ── Registrar todos los frames ────────────────
        self.frames = {}
        for F in ALL_FRAMES:
            name  = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ClinicaIndexFrame")

    # ──────────────────────────────────────────────────
    def _load_backgrounds(self):
        paths = {
            "flatly":    "sources/background.png",
            "superhero": "sources/background_black.png",
        }
        for theme, path in paths.items():
            try:
                if os.path.exists(path):
                    img = Image.open(path).resize((1000, 800))
                    self.background_images[theme] = ImageTk.PhotoImage(img)
                else:
                    self.background_images[theme] = None
            except Exception as e:
                self.background_images[theme] = None
                print(f"[WARN] No se pudo cargar fondo '{theme}': {e}")

        self.background_image = self.background_images.get("flatly")

    def _load_icon(self):
        icon_path = "sources/glucosa.png"
        try:
            if os.path.exists(icon_path):
                self.icon_photo = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, self.icon_photo)
        except Exception as e:
            print(f"[WARN] Ícono no disponible: {e}")

    # ──────────────────────────────────────────────────
    def show_frame(self, frame_name: str):
        frame = self.frames.get(frame_name)
        if frame:
            frame.tkraise()
        else:
            messagebox.showerror("Error", f"Frame '{frame_name}' no encontrado.")

    # ──────────────────────────────────────────────────
    def login(self, correo: str, contrasena: str):
        """Autenticación; redirige según rol y perfil seleccionado."""
        if not correo or not contrasena:
            messagebox.showwarning("Campos vacíos",
                                   "Por favor ingresa correo y contraseña.")
            return False

        conn   = sqlite3.connect("clinica_digital.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, apellidos, correo, rol "
            "FROM usuarios WHERE correo=? AND contrasena=? LIMIT 1",
            (correo, contrasena),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            self.current_user = {
                "id":        row[0],
                "nombre":    row[1],
                "apellidos": row[2],
                "correo":    row[3],
                "rol":       row[4],
            }
            # Redirigir según rol real almacenado en BD
            destinos = {
                "paciente": "PacienteMainFrame",
                "medico":   "MedicoMainFrame",
                "admin":    "AdminMainClinicaFrame",
            }
            dest = destinos.get(self.current_user["rol"], "ClinicaIndexFrame")
            self.show_frame(dest)
            return True
        else:
            messagebox.showerror("Error de acceso",
                                 "Correo o contraseña incorrectos.")
            return False

    # ──────────────────────────────────────────────────
    def logout(self):
        self.current_user = None
        self.login_rol    = None
        self.show_frame("ClinicaIndexFrame")

    # ──────────────────────────────────────────────────
    def toggle_theme(self):
        if self.theme_name == "flatly":
            self.style.theme_use("superhero")
            self.theme_name   = "superhero"
            self.background_image = self.background_images.get("superhero")
        else:
            self.style.theme_use("flatly")
            self.theme_name   = "flatly"
            self.background_image = self.background_images.get("flatly")

        # Actualizar fondo en todos los frames que heredan de BackgroundFrame
        for frame in self.frames.values():
            if isinstance(frame, BackgroundFrame):
                frame.update_background_image()


# ──────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ClinicaDigitalApp()
    app.mainloop()