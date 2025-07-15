# modules/db_init.py
import sqlite3
import bcrypt
from flask import current_app

def init_db(db_path, schema_path):
    """Inicializa una base de datos usando un archivo de esquema SQL."""
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Base de datos en '{db_path}' inicializada con esquema '{schema_path}'.")

def init_user_db(db_path):
    """Crea y llena la base de datos de usuarios con un admin por defecto."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Administrador', 'Ingeniero', 'Consultor'))
    )''')

    # --- AÑADIR USUARIO ADMIN POR DEFECTO ---
    try:
        # Hashear la contraseña por defecto 'admin'
        default_password = b'admin789'
        hashed_password = bcrypt.hashpw(default_password, bcrypt.gensalt())

        # Insertar el usuario administrador
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', hashed_password, 'Administrador')
        )
        print("Usuario 'admin' por defecto creado con éxito.")
    except sqlite3.IntegrityError:
        # El usuario ya existe, no hacer nada
        print("El usuario 'admin' ya existe.")

    conn.commit()
    conn.close()

def init_normative_db(db_path):
    """Crea y llena la base de datos normativa con datos iniciales."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear tabla de factores de corrección por temperatura
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS factores_correccion_temp (
        id INTEGER PRIMARY KEY,
        temp_min REAL NOT NULL,
        temp_max REAL NOT NULL,
        factor REAL NOT NULL
    )
    ''')

    # Crear tabla de ampacidad de cables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ampacidad_cables (
        id INTEGER PRIMARY KEY,
        calibre TEXT UNIQUE NOT NULL,
        ampacidad REAL NOT NULL
    )
    ''')

    # Crear tabla de reactancia y resistencia de cables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reactancia_resistencia_cables (
        id INTEGER PRIMARY KEY,
        calibre TEXT UNIQUE NOT NULL,
        resistencia REAL NOT NULL,
        reactancia REAL NOT NULL
    )
    ''')

    # --- INSERTAR DATOS INICIALES ---
    # (Solo si las tablas están vacías para evitar duplicados)

    # Datos para factores de corrección
    factores_temp = [
        (21, 25, 1.08),
        (26, 30, 1.00),
        (31, 35, 0.91),
        (36, 40, 0.82),
        (41, 45, 0.71),
        (46, 50, 0.58)
    ]
    cursor.execute("SELECT COUNT(*) FROM factores_correccion_temp")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO factores_correccion_temp (temp_min, temp_max, factor) VALUES (?, ?, ?)", factores_temp)

    # Datos para ampacidad de cables (ejemplo)
    ampacidad = [
        ('14 AWG', 20),
        ('12 AWG', 25),
        ('10 AWG', 30),
        ('8 AWG', 40),
        ('6 AWG', 55),
        ('4 AWG', 70),
        ('2 AWG', 95),
        ('1/0', 125),
        ('2/0', 145),
        ('3/0', 165),
        ('4/0', 195)
    ]
    cursor.execute("SELECT COUNT(*) FROM ampacidad_cables")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ampacidad_cables (calibre, ampacidad) VALUES (?, ?)", ampacidad)

    # Datos para resistencia y reactancia (ejemplo)
    res_react = [
        ('14 AWG', 8.69, 0.18),
        ('12 AWG', 5.48, 0.18),
        ('10 AWG', 3.44, 0.17),
        ('8 AWG', 2.16, 0.17),
        ('6 AWG', 1.36, 0.16),
        ('4 AWG', 0.85, 0.16),
        ('2 AWG', 0.54, 0.15),
        ('1/0', 0.34, 0.15),
        ('2/0', 0.27, 0.14),
        ('3/0', 0.21, 0.14),
        ('4/0', 0.17, 0.14)
    ]
    cursor.execute("SELECT COUNT(*) FROM reactancia_resistencia_cables")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO reactancia_resistencia_cables (calibre, resistencia, reactancia) VALUES (?, ?, ?)", res_react)

    conn.commit()
    conn.close()
    print("Base de datos normativa inicializada con éxito.")

