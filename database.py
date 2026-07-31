from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from security import hash_password, verify_password, validate_password, reset_code, token_hash, PREFIX

DB_NAME = Path(__file__).with_name("clinica_digital.db")

# Política central de agenda: días hábiles, horario y duración de cada espacio.
BUSINESS_HOURS = {day: ("09:00", "17:00") for day in range(5)}
APPOINTMENT_MINUTES = 30
CHECK_IN_EARLY_MINUTES = 30
CHECK_IN_LATE_MINUTES = 15


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Abre una conexión transaccional y revierte cambios ante errores."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def setup_database() -> None:
    """Crea el esquema y migra credenciales heredadas al formato seguro."""
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('paciente','medico','admin')),
            telefono TEXT,
            fecha_nac TEXT,
            tipo_sangre TEXT,
            alergias TEXT,
            creado_en TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id),
            especialidad TEXT NOT NULL,
            cedula TEXT,
            max_citas_dia INTEGER DEFAULT 20
        );
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES usuarios(id),
            medico_id INTEGER NOT NULL REFERENCES medicos(id),
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            modalidad TEXT NOT NULL CHECK(modalidad IN ('presencial','telemedicina')),
            motivo TEXT,
            estado TEXT NOT NULL DEFAULT 'confirmada'
                CHECK(estado IN ('confirmada','en_espera','completada','cancelada','no_show')),
            version INTEGER DEFAULT 0,
            creado_en TEXT DEFAULT (datetime('now')),
            UNIQUE(medico_id, fecha, hora)
        );
        CREATE TABLE IF NOT EXISTS expedientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES usuarios(id),
            fecha_visita TEXT NOT NULL,
            medico_id INTEGER REFERENCES medicos(id),
            diagnostico TEXT,
            notas TEXT,
            creado_en TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente_id INTEGER REFERENCES expedientes(id),
            paciente_id INTEGER NOT NULL REFERENCES usuarios(id),
            medico_id INTEGER REFERENCES medicos(id),
            medicamento TEXT NOT NULL,
            dosis TEXT,
            frecuencia TEXT,
            duracion TEXT,
            indicaciones TEXT,
            fecha_emision TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS signos_vitales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES usuarios(id),
            cita_id INTEGER REFERENCES citas(id),
            temperatura REAL,
            presion_sistol INTEGER,
            presion_diast INTEGER,
            frec_cardiaca INTEGER,
            saturacion_o2 REAL,
            peso_kg REAL,
            sintomas TEXT,
            registrado_en TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cola_espera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id INTEGER NOT NULL UNIQUE REFERENCES citas(id),
            turno INTEGER NOT NULL,
            prioridad TEXT DEFAULT 'normal' CHECK(prioridad IN ('normal','urgencia','adulto_mayor')),
            estado TEXT DEFAULT 'en_espera' CHECK(estado IN ('en_espera','en_consulta','completado')),
            hora_llegada TEXT DEFAULT (datetime('now')),
            hora_llamado TEXT
        );
        CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id INTEGER REFERENCES citas(id),
            paciente_id INTEGER REFERENCES usuarios(id),
            tipo TEXT CHECK(tipo IN ('24h','1h','cancelacion','turno')),
            canal TEXT CHECK(canal IN ('sms','email','push','app')),
            enviado INTEGER DEFAULT 0,
            enviado_en TEXT
        );
        """)
        if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            _seed(conn)

        conn.execute("""CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL,
            expira_en TEXT NOT NULL,
            usado INTEGER NOT NULL DEFAULT 0,
            creado_en TEXT DEFAULT (datetime('now'))
        )""")

        # Migra automáticamente contraseñas anteriores guardadas en texto plano.
        for row in conn.execute("SELECT id,contrasena FROM usuarios").fetchall():
            if row["contrasena"] and not row["contrasena"].startswith(PREFIX + "$"):
                conn.execute("UPDATE usuarios SET contrasena=? WHERE id=?",
                             (hash_password(row["contrasena"]), row["id"]))


def _seed(conn: sqlite3.Connection) -> None:
    users = [
        ("Recepción", "Administración", "admin@clinica.mx", "admin123", "admin", "3310000000", None, None, None),
        ("Carlos", "Ramírez Torres", "cramires@clinica.mx", "medico123", "medico", "3311000001", "1980-05-10", None, None),
        ("Laura", "López Vega", "llopez@clinica.mx", "medico123", "medico", "3311000002", "1975-08-22", None, None),
        ("Pedro", "Torres Soto", "ptorres@clinica.mx", "medico123", "medico", "3311000003", "1982-11-03", None, None),
        ("Juan", "Pérez García", "juan@mail.com", "paciente1", "paciente", "3312001001", "1990-04-12", "O+", "Penicilina"),
        ("Ana", "Torres Ruiz", "ana@mail.com", "paciente1", "paciente", "3312001002", "1976-08-15", "A+", "Ninguna"),
        ("Carlos", "Vega López", "carlos@mail.com", "paciente1", "paciente", "3312001003", "1963-02-01", "B-", "Sulfas"),
        ("María", "Gómez Soto", "maria@mail.com", "paciente1", "paciente", "3312001004", "1995-07-30", "AB+", "Ninguna"),
        ("Rosa", "Medina Cruz", "rosa@mail.com", "paciente1", "paciente", "3312001005", "1958-12-20", "O-", "Ibuprofeno"),
    ]
    conn.executemany("""INSERT INTO usuarios
        (nombre,apellidos,correo,contrasena,rol,telefono,fecha_nac,tipo_sangre,alergias)
        VALUES (?,?,?,?,?,?,?,?,?)""", users)
    conn.executemany("INSERT INTO medicos(usuario_id,especialidad,cedula,max_citas_dia) VALUES(?,?,?,?)", [
        (2, "Medicina General", "CED-001", 20), (3, "Cardiología", "CED-002", 15), (4, "Neurología", "CED-003", 12)
    ])
    today = date.today()
    appointments = [
        (5, 1, str(today), "09:00", "presencial", "Revisión diabetes", "completada"),
        (6, 2, str(today), "10:00", "telemedicina", "Control HTA", "confirmada"),
        (7, 1, str(today), "10:30", "presencial", "Cefalea recurrente", "en_espera"),
        (8, 1, str(today), "11:00", "presencial", "Revisión general", "no_show"),
        (9, 3, str(today + timedelta(days=1)), "09:30", "presencial", "Seguimiento EPOC", "confirmada"),
        (5, 2, str(today + timedelta(days=2)), "11:00", "telemedicina", "Dolor de cabeza", "confirmada"),
    ]
    conn.executemany("INSERT INTO citas(paciente_id,medico_id,fecha,hora,modalidad,motivo,estado) VALUES(?,?,?,?,?,?,?)", appointments)
    conn.executemany("INSERT INTO expedientes(paciente_id,fecha_visita,medico_id,diagnostico,notas) VALUES(?,?,?,?,?)", [
        (5, str(today - timedelta(days=35)), 1, "Diabetes tipo 2 controlada", "Continúa metformina 850 mg"),
        (5, str(today - timedelta(days=82)), 2, "Hipertensión arterial", "Losartán 50 mg cada 24 h"),
        (6, str(today - timedelta(days=20)), 2, "HTA crónica en seguimiento", "Ajuste de dosis"),
    ])
    conn.executemany("INSERT INTO recetas(expediente_id,paciente_id,medico_id,medicamento,dosis,frecuencia,duracion,indicaciones) VALUES(?,?,?,?,?,?,?,?)", [
        (1, 5, 1, "Metformina 850 mg", "1 tableta", "Cada 8 horas", "30 días", "Tomar con alimentos"),
        (2, 5, 2, "Losartán 50 mg", "1 tableta", "Cada 24 horas", "60 días", "En ayunas"),
    ])
    conn.executemany("INSERT INTO signos_vitales(paciente_id,cita_id,temperatura,presion_sistol,presion_diast,frec_cardiaca,saturacion_o2,peso_kg,sintomas) VALUES(?,?,?,?,?,?,?,?,?)", [
        (5, 1, 36.6, 128, 82, 72, 98, 74, "Ligero dolor de cabeza"),
        (6, 2, 36.8, 130, 85, 76, 97.5, 68, "Sin síntomas"),
    ])
    conn.executemany("INSERT INTO cola_espera(cita_id,turno,prioridad,estado) VALUES(?,?,?,?)", [
        (1, 5, "normal", "completado"), (2, 6, "normal", "en_espera"), (3, 7, "normal", "en_espera"), (4, 8, "adulto_mayor", "en_espera")
    ])
    conn.executemany("INSERT INTO notificaciones(cita_id,paciente_id,tipo,canal,enviado) VALUES(?,?,?,?,?)", [
        (1, 5, "24h", "sms", 1), (2, 6, "1h", "app", 0), (3, 7, "24h", "email", 1)
    ])


def _rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def authenticate(email: str, password: str, expected_role: str | None = None) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("""SELECT id,nombre,apellidos,correo,rol,telefono,fecha_nac,
                           tipo_sangre,alergias,contrasena
                           FROM usuarios WHERE lower(correo)=lower(?)""",
                           (email.strip(),)).fetchone()
        if not row or (expected_role and row["rol"] != expected_role):
            return None
        if not verify_password(password, row["contrasena"]):
            return None
        user = {k: row[k] for k in ("id","nombre","apellidos","correo","rol",
                                     "telefono","fecha_nac","tipo_sangre","alergias")}
        if user["rol"] == "medico":
            med = conn.execute("SELECT id,especialidad,cedula FROM medicos WHERE usuario_id=?",
                               (user["id"],)).fetchone()
            if med:
                user.update({"medico_id": med["id"], "especialidad": med["especialidad"],
                             "cedula": med["cedula"]})
        return user


def list_doctors() -> list[dict[str, Any]]:
    return _rows("""SELECT m.id, u.nombre||' '||u.apellidos nombre, m.especialidad,
                    m.cedula, m.max_citas_dia
                    FROM medicos m JOIN usuarios u ON u.id=m.usuario_id ORDER BY m.especialidad,u.nombre""")


def appointment_policy_message() -> str:
    """Devuelve la política que se muestra al paciente."""
    return (
        "Horario: lunes a viernes de 09:00 a 17:00, en espacios de "
        f"{APPOINTMENT_MINUTES} minutos. Check-in desde "
        f"{CHECK_IN_EARLY_MINUTES} minutos antes y hasta "
        f"{CHECK_IN_LATE_MINUTES} minutos después."
    )


def appointment_hours() -> list[str]:
    """Genera los horarios del formulario desde la política central."""
    start = datetime.strptime("09:00", "%H:%M")
    end = datetime.strptime("17:00", "%H:%M")
    hours = []
    while start < end:
        hours.append(start.strftime("%H:%M"))
        start += timedelta(minutes=APPOINTMENT_MINUTES)
    return hours


def _valid_schedule(appointment_date: date, hour: str) -> bool:
    """Valida día hábil, rango de atención y bloques de media hora."""
    schedule = BUSINESS_HOURS.get(appointment_date.weekday())
    if not schedule:
        return False
    try:
        appointment_time = datetime.strptime(hour, "%H:%M").time()
    except ValueError:
        return False
    opening = datetime.strptime(schedule[0], "%H:%M").time()
    closing = datetime.strptime(schedule[1], "%H:%M").time()
    return opening <= appointment_time < closing and appointment_time.minute in (0, 30)


def get_patient_appointments(patient_id: int) -> list[dict[str, Any]]:
    return _rows("""SELECT c.id,c.fecha,c.hora,u.nombre||' '||u.apellidos medico,m.especialidad,
                    c.modalidad,c.motivo,c.estado FROM citas c JOIN medicos m ON m.id=c.medico_id
                    JOIN usuarios u ON u.id=m.usuario_id WHERE c.paciente_id=? ORDER BY c.fecha DESC,c.hora DESC""", (patient_id,))


def reserve_appointment(patient_id: int, doctor_id: int, appointment_date: str, hour: str, modality: str, reason: str) -> tuple[bool, str]:
    """Reserva una cita respetando horario y máximo diario del médico."""
    try:
        selected_date = date.fromisoformat(appointment_date)
    except (TypeError, ValueError):
        return False, "La fecha debe tener el formato AAAA-MM-DD."
    if selected_date < date.today():
        return False, "La fecha no puede estar en el pasado."
    if not _valid_schedule(selected_date, hour):
        return False, appointment_policy_message()
    if modality not in ("presencial", "telemedicina"):
        return False, "La modalidad seleccionada no es válida."
    if not reason.strip():
        return False, "Escribe el motivo de consulta."
    try:
        with connection() as conn:
            # El bloqueo impide que reservas simultáneas rebasen el cupo.
            conn.execute("BEGIN IMMEDIATE")
            doctor = conn.execute(
                "SELECT max_citas_dia FROM medicos WHERE id=?", (doctor_id,)
            ).fetchone()
            if not doctor:
                return False, "El médico seleccionado no existe."
            booked = conn.execute(
                """SELECT COUNT(*) FROM citas
                   WHERE medico_id=? AND fecha=? AND estado!='cancelada'""",
                (doctor_id, appointment_date),
            ).fetchone()[0]
            if booked >= doctor["max_citas_dia"]:
                return False, (
                    f"El médico alcanzó su máximo de {doctor['max_citas_dia']} "
                    "citas para ese día. Selecciona otra fecha."
                )
            conn.execute("INSERT INTO citas(paciente_id,medico_id,fecha,hora,modalidad,motivo,estado) VALUES(?,?,?,?,?,?, 'confirmada')",
                         (patient_id, doctor_id, appointment_date, hour, modality, reason.strip()))
        return True, "Cita agendada correctamente."
    except sqlite3.IntegrityError:
        return False, "Ese horario ya está ocupado. Selecciona otro."


def check_in_appointment(
    appointment_id: int,
    patient_id: int,
    priority: str = "normal",
) -> tuple[bool, str, int | None]:
    """Registra la llegada y asigna el siguiente turno de forma atómica."""
    if priority not in ("normal", "urgencia", "adulto_mayor"):
        return False, "La prioridad no es válida.", None
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        appointment = conn.execute(
            """SELECT c.id,c.fecha,c.hora,c.modalidad,c.estado,u.fecha_nac
               FROM citas c JOIN usuarios u ON u.id=c.paciente_id
               WHERE c.id=? AND c.paciente_id=?""",
            (appointment_id, patient_id),
        ).fetchone()
        if not appointment:
            return False, "La cita no existe.", None
        if appointment["modalidad"] != "presencial":
            return False, "El check-in solo aplica a citas presenciales.", None
        if appointment["estado"] != "confirmada":
            existing = conn.execute(
                "SELECT turno FROM cola_espera WHERE cita_id=?", (appointment_id,)
            ).fetchone()
            if existing:
                return True, f"Check-in ya registrado: turno #{existing['turno']}.", existing["turno"]
            return False, "Esta cita ya no admite check-in.", None

        # La prioridad de adulto mayor se obtiene del expediente y no depende
        # de que el paciente la solicite manualmente.
        if priority == "normal" and appointment["fecha_nac"]:
            birth_date = date.fromisoformat(appointment["fecha_nac"])
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            if age >= 60:
                priority = "adulto_mayor"

        appointment_at = datetime.fromisoformat(
            f"{appointment['fecha']}T{appointment['hora']}:00"
        )
        now = datetime.now()
        window_start = appointment_at - timedelta(minutes=CHECK_IN_EARLY_MINUTES)
        window_end = appointment_at + timedelta(minutes=CHECK_IN_LATE_MINUTES)
        if not window_start <= now <= window_end:
            return False, (
                f"Puedes hacer check-in de {window_start:%H:%M} a "
                f"{window_end:%H:%M} el {appointment_at:%Y-%m-%d}."
            ), None

        # Los turnos son consecutivos por día, no globales.
        next_turn = conn.execute(
            """SELECT COALESCE(MAX(q.turno), 0) + 1
               FROM cola_espera q JOIN citas c ON c.id=q.cita_id
               WHERE c.fecha=?""",
            (appointment["fecha"],),
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO cola_espera(cita_id,turno,prioridad,estado)
               VALUES(?,?,?,'en_espera')""",
            (appointment_id, next_turn, priority),
        )
        conn.execute(
            "UPDATE citas SET estado='en_espera',version=version+1 WHERE id=?",
            (appointment_id,),
        )
        conn.execute(
            """INSERT INTO notificaciones(cita_id,paciente_id,tipo,canal)
               VALUES(?,?,'turno','app')""",
            (appointment_id, patient_id),
        )
        return True, f"Check-in listo. Tu turno es #{next_turn}.", next_turn


def cancel_appointment(appointment_id: int, patient_id: int) -> bool:
    with connection() as conn:
        cur = conn.execute("UPDATE citas SET estado='cancelada',version=version+1 WHERE id=? AND paciente_id=? AND estado IN ('confirmada','en_espera')", (appointment_id, patient_id))
        return cur.rowcount > 0


def get_patient_record(patient_id: int) -> list[dict[str, Any]]:
    return _rows("""SELECT e.id,e.fecha_visita,u.nombre||' '||u.apellidos medico,e.diagnostico,e.notas
                    FROM expedientes e LEFT JOIN medicos m ON m.id=e.medico_id LEFT JOIN usuarios u ON u.id=m.usuario_id
                    WHERE e.paciente_id=? ORDER BY e.fecha_visita DESC""", (patient_id,))


def get_patient_prescriptions(patient_id: int) -> list[dict[str, Any]]:
    return _rows("""SELECT r.fecha_emision,r.medicamento,r.dosis,r.frecuencia,r.duracion,r.indicaciones,
                    u.nombre||' '||u.apellidos medico FROM recetas r LEFT JOIN medicos m ON m.id=r.medico_id
                    LEFT JOIN usuarios u ON u.id=m.usuario_id WHERE r.paciente_id=? ORDER BY r.fecha_emision DESC""", (patient_id,))


def save_vitals(patient_id: int, data: dict[str, Any]) -> None:
    with connection() as conn:
        conn.execute("""INSERT INTO signos_vitales(paciente_id,temperatura,presion_sistol,presion_diast,frec_cardiaca,saturacion_o2,peso_kg,sintomas)
                        VALUES(?,?,?,?,?,?,?,?)""", (patient_id, data["temperatura"], data["sistolica"], data["diastolica"], data["cardiaca"], data["saturacion"], data["peso"], data["sintomas"]))


def get_queue_for_patient(patient_id: int) -> dict[str, Any] | None:
    rows = _rows("""SELECT q.turno,q.prioridad,q.estado,c.fecha,c.hora FROM cola_espera q JOIN citas c ON c.id=q.cita_id
                    WHERE c.paciente_id=? AND q.estado!='completado' ORDER BY c.fecha,c.hora LIMIT 1""", (patient_id,))
    return rows[0] if rows else None


def get_doctor_agenda(doctor_id: int) -> list[dict[str, Any]]:
    return _rows("""SELECT c.id,c.hora,u.nombre||' '||u.apellidos paciente,c.motivo,c.modalidad,c.estado,c.paciente_id
                    FROM citas c JOIN usuarios u ON u.id=c.paciente_id WHERE c.medico_id=? AND c.fecha=? ORDER BY c.hora""", (doctor_id, str(date.today())))


def list_patients(search: str = "") -> list[dict[str, Any]]:
    term = f"%{search.strip()}%"
    return _rows("""SELECT id,nombre||' '||apellidos nombre,correo,telefono,fecha_nac,tipo_sangre,alergias
                    FROM usuarios WHERE rol='paciente' AND (nombre||' '||apellidos LIKE ? OR correo LIKE ?) ORDER BY nombre""", (term, term))


def get_latest_vitals() -> list[dict[str, Any]]:
    return _rows("""SELECT s.registrado_en,u.nombre||' '||u.apellidos paciente,s.temperatura,
                    s.presion_sistol||'/'||s.presion_diast presion,s.frec_cardiaca,s.saturacion_o2,s.sintomas
                    FROM signos_vitales s JOIN usuarios u ON u.id=s.paciente_id ORDER BY s.registrado_en DESC LIMIT 25""")


def create_prescription(doctor_id: int, patient_id: int, medication: str, dose: str, frequency: str, duration: str, instructions: str) -> None:
    with connection() as conn:
        conn.execute("INSERT INTO recetas(paciente_id,medico_id,medicamento,dosis,frecuencia,duracion,indicaciones) VALUES(?,?,?,?,?,?,?)",
                     (patient_id, doctor_id, medication, dose, frequency, duration, instructions))


def get_all_appointments() -> list[dict[str, Any]]:
    return _rows("""SELECT c.id,c.fecha,c.hora,p.nombre||' '||p.apellidos paciente,d.nombre||' '||d.apellidos medico,
                    m.especialidad,c.modalidad,c.estado FROM citas c JOIN usuarios p ON p.id=c.paciente_id
                    JOIN medicos m ON m.id=c.medico_id JOIN usuarios d ON d.id=m.usuario_id ORDER BY c.fecha DESC,c.hora""")


def get_kpis() -> dict[str, Any]:
    with connection() as conn:
        today = str(date.today())
        total = conn.execute("SELECT COUNT(*) FROM citas WHERE fecha=?", (today,)).fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM citas WHERE fecha=? AND estado='completada'", (today,)).fetchone()[0]
        waiting = conn.execute("SELECT COUNT(*) FROM cola_espera WHERE estado='en_espera'").fetchone()[0]
        no_show = conn.execute("SELECT COUNT(*) FROM citas WHERE fecha=? AND estado='no_show'", (today,)).fetchone()[0]
        patients = conn.execute("SELECT COUNT(*) FROM usuarios WHERE rol='paciente'").fetchone()[0]
        tele = conn.execute("SELECT COUNT(*) FROM citas WHERE fecha=? AND modalidad='telemedicina'", (today,)).fetchone()[0]
        return {"citas_hoy": total, "completadas": completed, "en_espera": waiting, "no_show": no_show, "pacientes": patients, "telemedicina": tele}


def get_queue() -> list[dict[str, Any]]:
    return _rows("""SELECT q.id,q.turno,p.nombre||' '||p.apellidos paciente,d.nombre||' '||d.apellidos medico,
                    q.prioridad,q.estado,q.hora_llegada FROM cola_espera q JOIN citas c ON c.id=q.cita_id
                    JOIN usuarios p ON p.id=c.paciente_id JOIN medicos m ON m.id=c.medico_id JOIN usuarios d ON d.id=m.usuario_id
                    ORDER BY CASE q.prioridad WHEN 'urgencia' THEN 0 WHEN 'adulto_mayor' THEN 1 ELSE 2 END,q.turno""")


def update_queue(queue_id: int, state: str) -> None:
    with connection() as conn:
        conn.execute("UPDATE cola_espera SET estado=?,hora_llamado=CASE WHEN ?='en_consulta' THEN datetime('now') ELSE hora_llamado END WHERE id=?", (state, state, queue_id))


def get_notifications() -> list[dict[str, Any]]:
    return _rows("""SELECT n.id,p.nombre||' '||p.apellidos paciente,n.tipo,n.canal,n.enviado,n.enviado_en,c.fecha,c.hora
                    FROM notificaciones n LEFT JOIN usuarios p ON p.id=n.paciente_id LEFT JOIN citas c ON c.id=n.cita_id ORDER BY n.id DESC""")


def mark_notification_sent(notification_id: int) -> None:
    with connection() as conn:
        conn.execute("UPDATE notificaciones SET enviado=1,enviado_en=datetime('now') WHERE id=?", (notification_id,))

# ========================= SEGURIDAD Y RECUPERACIÓN =========================

def create_password_reset_code(email: str) -> str | None:
    with connection() as conn:
        user = conn.execute("SELECT id FROM usuarios WHERE lower(correo)=lower(?)", (email.strip(),)).fetchone()
        if not user:
            return None
        code = reset_code()
        expires = datetime.now() + timedelta(minutes=15)
        conn.execute("UPDATE password_reset_tokens SET usado=1 WHERE usuario_id=? AND usado=0", (user["id"],))
        conn.execute("INSERT INTO password_reset_tokens(usuario_id,token_hash,expira_en) VALUES(?,?,?)",
                     (user["id"], token_hash(code), expires.isoformat(timespec="seconds")))
        return code


def reset_password(email: str, code: str, new_password: str) -> tuple[bool, str]:
    ok, message = validate_password(new_password)
    if not ok:
        return False, message
    with connection() as conn:
        user = conn.execute("SELECT id FROM usuarios WHERE lower(correo)=lower(?)", (email.strip(),)).fetchone()
        if not user:
            return False, "No se pudo restablecer la contraseña."
        token = conn.execute("""SELECT id,expira_en FROM password_reset_tokens
                                WHERE usuario_id=? AND token_hash=? AND usado=0
                                ORDER BY id DESC LIMIT 1""",
                             (user["id"], token_hash(code))).fetchone()
        if not token:
            return False, "Código incorrecto o ya utilizado."
        if datetime.fromisoformat(token["expira_en"]) < datetime.now():
            return False, "El código expiró."
        conn.execute("UPDATE usuarios SET contrasena=? WHERE id=?", (hash_password(new_password), user["id"]))
        conn.execute("UPDATE password_reset_tokens SET usado=1 WHERE id=?", (token["id"],))
        return True, "Contraseña actualizada correctamente."


# =============================== CRUD PACIENTES ==============================

def create_patient(data: dict[str, Any]) -> tuple[bool, str]:
    ok, message = validate_password(data.get("contrasena", ""))
    if not ok:
        return False, message
    try:
        with connection() as conn:
            conn.execute("""INSERT INTO usuarios
                (nombre,apellidos,correo,contrasena,rol,telefono,fecha_nac,tipo_sangre,alergias)
                VALUES(?,?,?,?, 'paciente',?,?,?,?)""",
                (data["nombre"].strip(), data["apellidos"].strip(), data["correo"].strip().lower(),
                 hash_password(data["contrasena"]), data.get("telefono", "").strip(),
                 data.get("fecha_nac", "").strip() or None, data.get("tipo_sangre", "").strip() or None,
                 data.get("alergias", "").strip() or None))
        return True, "Paciente creado correctamente."
    except sqlite3.IntegrityError:
        return False, "Ese correo ya está registrado."


def get_patient(patient_id: int) -> dict[str, Any] | None:
    rows = _rows("""SELECT id,nombre,apellidos,correo,telefono,fecha_nac,tipo_sangre,alergias
                    FROM usuarios WHERE id=? AND rol='paciente'""", (patient_id,))
    return rows[0] if rows else None


def update_patient(patient_id: int, data: dict[str, Any]) -> tuple[bool, str]:
    try:
        with connection() as conn:
            cur = conn.execute("""UPDATE usuarios SET nombre=?,apellidos=?,correo=?,telefono=?,
                                  fecha_nac=?,tipo_sangre=?,alergias=?
                                  WHERE id=? AND rol='paciente'""",
                (data["nombre"].strip(), data["apellidos"].strip(), data["correo"].strip().lower(),
                 data.get("telefono", "").strip(), data.get("fecha_nac", "").strip() or None,
                 data.get("tipo_sangre", "").strip() or None, data.get("alergias", "").strip() or None,
                 patient_id))
            if cur.rowcount == 0:
                return False, "Paciente no encontrado."
        return True, "Paciente actualizado correctamente."
    except sqlite3.IntegrityError:
        return False, "Ese correo pertenece a otro usuario."


def delete_patient(patient_id: int) -> tuple[bool, str]:
    # No elimina expedientes: bloquea el acceso cambiando el correo y contraseña.
    with connection() as conn:
        cur = conn.execute("""UPDATE usuarios
                              SET correo='inactivo_'||id||'_'||correo, contrasena=?
                              WHERE id=? AND rol='paciente'""",
                           (hash_password(reset_code() + "Aa1"), patient_id))
        return (cur.rowcount > 0, "Paciente desactivado." if cur.rowcount else "Paciente no encontrado.")


# ========================== HISTORIAL SIGNOS VITALES =========================

def get_patient_vitals(patient_id: int, limit: int = 100) -> list[dict[str, Any]]:
    return _rows("""SELECT id,registrado_en,temperatura,presion_sistol,presion_diast,
                           frec_cardiaca,saturacion_o2,peso_kg,sintomas
                    FROM signos_vitales WHERE paciente_id=?
                    ORDER BY registrado_en DESC,id DESC LIMIT ?""", (patient_id, limit))
