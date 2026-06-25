"""
database_clinica.py
Inicialización de la base de datos SQLite para Clínica-Digital.
Crea tablas, restricciones e inserta datos de prueba.
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
import random


DB_NAME = "clinica_digital.db"


def setup_database():
    conn   = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ──────────────────────────────────────────────
    # PRAGMA: integridad referencial activada
    # ──────────────────────────────────────────────
    cursor.execute("PRAGMA foreign_keys = ON")

    # ──────────────────────────────────────────────
    # TABLA: usuarios  (paciente | medico | admin)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            apellidos   TEXT    NOT NULL,
            correo      TEXT    NOT NULL UNIQUE,
            contrasena  TEXT    NOT NULL,
            rol         TEXT    NOT NULL CHECK(rol IN ('paciente','medico','admin')),
            telefono    TEXT,
            fecha_nac   TEXT,
            tipo_sangre TEXT,
            alergias    TEXT,
            creado_en   TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: medicos  (perfil extendido)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
            especialidad    TEXT    NOT NULL,
            cedula          TEXT,
            max_citas_dia   INTEGER DEFAULT 20
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: horarios_medico
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS horarios_medico (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            medico_id   INTEGER NOT NULL REFERENCES medicos(id),
            dia_semana  INTEGER NOT NULL,   -- 0=Lun … 6=Dom
            hora_inicio TEXT    NOT NULL,
            hora_fin    TEXT    NOT NULL
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: citas
    #   version → bloqueo optimista (RQ-001)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL REFERENCES usuarios(id),
            medico_id       INTEGER NOT NULL REFERENCES medicos(id),
            fecha           TEXT    NOT NULL,
            hora            TEXT    NOT NULL,
            modalidad       TEXT    NOT NULL CHECK(modalidad IN ('presencial','telemedicina')),
            motivo          TEXT,
            estado          TEXT    NOT NULL
                            CHECK(estado IN ('confirmada','en_espera','completada',
                                             'cancelada','no_show'))
                            DEFAULT 'en_espera',
            version         INTEGER DEFAULT 0,       -- optimistic locking RQ-001
            creado_en       TEXT    DEFAULT (datetime('now')),
            UNIQUE(medico_id, fecha, hora)           -- previene doble reserva
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: expedientes
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expedientes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL REFERENCES usuarios(id),
            fecha_visita    TEXT    NOT NULL,
            medico_id       INTEGER REFERENCES medicos(id),
            diagnostico     TEXT,
            notas           TEXT,
            hash_sha256     TEXT,   -- integridad RQ-002
            creado_en       TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: recetas
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recetas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente_id   INTEGER REFERENCES expedientes(id),
            paciente_id     INTEGER NOT NULL REFERENCES usuarios(id),
            medico_id       INTEGER REFERENCES medicos(id),
            medicamento     TEXT    NOT NULL,
            dosis           TEXT,
            frecuencia      TEXT,
            duracion        TEXT,
            indicaciones    TEXT,
            fecha_emision   TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: signos_vitales  (RQ-007)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signos_vitales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL REFERENCES usuarios(id),
            cita_id         INTEGER REFERENCES citas(id),
            temperatura     REAL,
            presion_sistol  INTEGER,
            presion_diast   INTEGER,
            frec_cardiaca   INTEGER,
            saturacion_o2   REAL,
            peso_kg         REAL,
            sintomas        TEXT,
            registrado_en   TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: cola_espera  (RQ-005)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cola_espera (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id         INTEGER NOT NULL REFERENCES citas(id),
            turno           INTEGER NOT NULL,
            prioridad       TEXT    DEFAULT 'normal'
                            CHECK(prioridad IN ('normal','urgencia','adulto_mayor')),
            estado          TEXT    DEFAULT 'en_espera'
                            CHECK(estado IN ('en_espera','en_consulta','completado')),
            hora_llegada    TEXT    DEFAULT (datetime('now')),
            hora_llamado    TEXT
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: sesiones_telemedicina  (RQ-003 / RQ-008)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiones_telemedicina (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id         INTEGER NOT NULL REFERENCES citas(id),
            inicio          TEXT,
            fin             TEXT,
            latencia_ms     INTEGER,
            estado          TEXT    DEFAULT 'activa'
                            CHECK(estado IN ('activa','finalizada','error')),
            reconexiones    INTEGER DEFAULT 0
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: notificaciones  (RQ-004)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id         INTEGER REFERENCES citas(id),
            paciente_id     INTEGER REFERENCES usuarios(id),
            tipo            TEXT    CHECK(tipo IN ('24h','1h','cancelacion','turno')),
            canal           TEXT    CHECK(canal IN ('sms','email','push','app')),
            enviado         INTEGER DEFAULT 0,  -- 0=pendiente 1=enviado
            enviado_en      TEXT
        )
    """)

    # ──────────────────────────────────────────────
    # TABLA: bitacora_acceso  (RQ-009)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_acceso (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id      INTEGER REFERENCES usuarios(id),
            expediente_id   INTEGER REFERENCES expedientes(id),
            operacion       TEXT    CHECK(operacion IN ('consulta','modificacion','descarga')),
            timestamp       TEXT    DEFAULT (datetime('now')),
            hmac_sha256     TEXT    -- inmutabilidad RQ-009
        )
    """)

    conn.commit()

    # ──────────────────────────────────────────────
    # DATOS DE PRUEBA (solo si la tabla está vacía)
    # ──────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        _seed_data(cursor)
        conn.commit()

    conn.close()
    print("[DB] Base de datos Clínica-Digital lista.")


def _seed_data(cursor):
    """Inserta usuarios, médicos, citas y expedientes de ejemplo."""

    # Usuarios: 1 admin, 3 médicos, 5 pacientes
    usuarios = [
        # (nombre, apellidos, correo, contrasena, rol, telefono, fecha_nac, tipo_sangre, alergias)
        ("Recepción", "Administración", "admin@clinica.mx",     "admin123",   "admin",    "3310000000", None, None, None),
        ("Carlos",    "Ramírez Torres", "cramires@clinica.mx",  "medico123",  "medico",   "3311000001", "1980-05-10", None, None),
        ("Laura",     "López Vega",     "llopez@clinica.mx",    "medico123",  "medico",   "3311000002", "1975-08-22", None, None),
        ("Pedro",     "Torres Soto",    "ptorres@clinica.mx",   "medico123",  "medico",   "3311000003", "1982-11-03", None, None),
        ("Juan",      "Pérez García",   "juan@mail.com",        "paciente1",  "paciente", "3312001001", "1990-04-12", "O+", "Penicilina"),
        ("Ana",       "Torres Ruiz",    "ana@mail.com",         "paciente1",  "paciente", "3312001002", "1976-08-15", "A+", "Ninguna"),
        ("Carlos",    "Vega López",     "carlos@mail.com",      "paciente1",  "paciente", "3312001003", "1963-02-01", "B-", "Sulfas"),
        ("María",     "Gómez Soto",     "maria@mail.com",       "paciente1",  "paciente", "3312001004", "1995-07-30", "AB+","Ninguna"),
        ("Rosa",      "Medina Cruz",    "rosa@mail.com",        "paciente1",  "paciente", "3312001005", "1958-12-20", "O-", "Ibuprofeno"),
    ]
    cursor.executemany(
        "INSERT INTO usuarios (nombre,apellidos,correo,contrasena,rol,telefono,"
        "fecha_nac,tipo_sangre,alergias) VALUES (?,?,?,?,?,?,?,?,?)",
        usuarios,
    )

    # Médicos (usuarios id 2,3,4 → médicos)
    medicos = [
        (2, "Medicina General",  "CED-001", 20),
        (3, "Cardiología",       "CED-002", 15),
        (4, "Neurología",        "CED-003", 12),
    ]
    cursor.executemany(
        "INSERT INTO medicos (usuario_id,especialidad,cedula,max_citas_dia) VALUES (?,?,?,?)",
        medicos,
    )

    # Citas de ejemplo
    hoy = datetime.now().date()
    citas = [
        (5, 1, str(hoy),                  "09:00", "presencial",   "Revisión diabetes",    "completada"),
        (6, 2, str(hoy),                  "10:00", "telemedicina", "Control HTA",          "confirmada"),
        (7, 1, str(hoy),                  "10:30", "presencial",   "Cefalea recurrente",   "en_espera"),
        (8, 1, str(hoy),                  "11:00", "presencial",   "Revisión general",     "no_show"),
        (9, 3, str(hoy + timedelta(days=1)),"09:30","presencial",  "Seguimiento EPOC",     "confirmada"),
        (5, 2, str(hoy + timedelta(days=2)),"11:00","telemedicina","Dolor de cabeza",      "confirmada"),
    ]
    cursor.executemany(
        "INSERT INTO citas (paciente_id,medico_id,fecha,hora,modalidad,motivo,estado) "
        "VALUES (?,?,?,?,?,?,?)",
        citas,
    )

    # Expedientes
    expedientes = [
        (5, "2025-05-28", 1, "Diabetes Tipo 2 controlada",   "Continúa metformina 850mg"),
        (5, "2025-04-10", 2, "Hipertensión arterial",        "Losartán 50mg c/24h"),
        (6, "2025-05-22", 2, "HTA crónica en seguimiento",   "Ajuste de dosis"),
        (7, "2025-05-15", 3, "EPOC leve",                    "Salbutamol según necesidad"),
        (8, "2025-06-01", 1, "Cefalea tensional",            "Paracetamol 500mg c/8h"),
    ]
    cursor.executemany(
        "INSERT INTO expedientes (paciente_id,fecha_visita,medico_id,diagnostico,notas) "
        "VALUES (?,?,?,?,?)",
        expedientes,
    )

    # Recetas
    recetas = [
        (1, 5, 1, "Metformina 850mg",  "1 tableta",  "Cada 8 horas",  "30 días", "Tomar con alimentos"),
        (2, 5, 2, "Losartán 50mg",     "1 tableta",  "Cada 24 horas", "60 días", "En ayunas"),
        (3, 6, 2, "Amlodipino 5mg",    "1 tableta",  "Cada 24 horas", "30 días", "Por la noche"),
    ]
    cursor.executemany(
        "INSERT INTO recetas (expediente_id,paciente_id,medico_id,medicamento,"
        "dosis,frecuencia,duracion,indicaciones) VALUES (?,?,?,?,?,?,?,?)",
        recetas,
    )

    # Signos vitales
    signos = [
        (5, 1, 36.6, 128, 82, 72, 98.0, 74.0, "Ligero dolor de cabeza"),
        (6, 2, 36.8, 130, 85, 76, 97.5, 68.0, "Sin síntomas"),
        (8, 4, 37.0, 120, 78, 80, 99.0, 61.0, "Leve mareo"),
    ]
    cursor.executemany(
        "INSERT INTO signos_vitales (paciente_id,cita_id,temperatura,presion_sistol,"
        "presion_diast,frec_cardiaca,saturacion_o2,peso_kg,sintomas) VALUES (?,?,?,?,?,?,?,?,?)",
        signos,
    )

    # Cola de espera
    cursor.executemany(
        "INSERT INTO cola_espera (cita_id,turno,prioridad,estado) VALUES (?,?,?,?)",
        [(1,5,"normal","completado"),
         (2,6,"normal","en_espera"),
         (3,7,"normal","en_espera"),
         (4,8,"adulto_mayor","en_espera")],
    )

    # Notificaciones
    cursor.executemany(
        "INSERT INTO notificaciones (cita_id,paciente_id,tipo,canal,enviado) VALUES (?,?,?,?,?)",
        [(1,5,"24h","sms",1),(1,5,"1h","app",1),
         (2,6,"24h","sms",1),(2,6,"1h","app",0),
         (3,7,"24h","email",1)],
    )

    print("[DB] Datos de prueba insertados correctamente.")


# ──────────────────────────────────────────────────────────────────
# Utilidades de consulta reutilizables por los frames
# ──────────────────────────────────────────────────────────────────

def get_citas_paciente(paciente_id: int) -> list:
    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.fecha, c.hora, u.nombre||' '||u.apellidos AS medico,
               m.especialidad, c.modalidad, c.estado
        FROM citas c
        JOIN medicos  m ON m.id = c.medico_id
        JOIN usuarios u ON u.id = m.usuario_id
        WHERE c.paciente_id = ?
        ORDER BY c.fecha DESC, c.hora DESC
    """, (paciente_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_citas_medico_hoy(medico_id: int) -> list:
    hoy = str(datetime.now().date())
    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.hora,
               u.nombre||' '||u.apellidos AS paciente,
               c.motivo, c.modalidad, c.estado
        FROM citas c
        JOIN usuarios u ON u.id = c.paciente_id
        WHERE c.medico_id = ? AND c.fecha = ?
        ORDER BY c.hora
    """, (medico_id, hoy))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_expediente_paciente(paciente_id: int) -> list:
    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()
    cur.execute("""
        SELECT e.fecha_visita,
               u.nombre||' '||u.apellidos AS medico,
               e.diagnostico, e.notas
        FROM expedientes e
        LEFT JOIN medicos  m ON m.id = e.medico_id
        LEFT JOIN usuarios u ON u.id = m.usuario_id
        WHERE e.paciente_id = ?
        ORDER BY e.fecha_visita DESC
    """, (paciente_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def reservar_cita(paciente_id, medico_id, fecha, hora, modalidad, motivo) -> bool:
    """
    RQ-001: intento de reserva con bloqueo único (UNIQUE medico_id+fecha+hora).
    Retorna True si tuvo éxito, False si el slot ya está ocupado.
    """
    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO citas (paciente_id, medico_id, fecha, hora, modalidad, motivo, estado)
            VALUES (?,?,?,?,?,?,'confirmada')
        """, (paciente_id, medico_id, fecha, hora, modalidad, motivo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False          # Slot ya ocupado
    finally:
        conn.close()


def get_kpis_hoy() -> dict:
    hoy = str(datetime.now().date())
    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM citas WHERE fecha=?", (hoy,))
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM citas WHERE fecha=? AND estado='completada'", (hoy,))
    atendidas = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM citas WHERE fecha=? AND estado='no_show'", (hoy,))
    noshows = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM citas WHERE fecha=? AND modalidad='telemedicina'", (hoy,))
    telemed = cur.fetchone()[0]

    conn.close()
    return {
        "total":     total,
        "atendidas": atendidas,
        "no_shows":  noshows,
        "telemed":   telemed,
        "ocupacion": round((atendidas / total * 100) if total else 0, 1),
    }


if __name__ == "__main__":
    setup_database()
    print("KPIs de hoy:", get_kpis_hoy())