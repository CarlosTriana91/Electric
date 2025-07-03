"""Módulo de Inicialización de Bases de Datos

Este módulo se encarga de crear y configurar las bases de datos necesarias
para el funcionamiento del sistema. Utiliza SQLite como motor de base de datos
por su simplicidad y portabilidad.
"""

import sqlite3  # Motor de base de datos SQL ligero y autocontenido
from functools import lru_cache  # Para optimización de rendimiento

@lru_cache(maxsize=128)
def get_normative_data(data_type, **kwargs):
    """Obtiene datos normativos de la base de datos con sistema de caché.

    Esta función implementa un sistema de caché para optimizar el acceso a datos
    normativos frecuentemente consultados. Soporta cuatro tipos de consultas:

    1. Ampacidad de conductores
       Requiere: calibre, material, temp_aislante
       Retorna: ampacidad en amperios

    2. Factor de corrección por temperatura
       Requiere: temp_ambiente
       Retorna: factor de corrección

    3. Factor de corrección por agrupamiento
       Requiere: num_conductores
       Retorna: factor de reducción

    4. Características eléctricas
       Requiere: calibre
       Retorna: (resistencia, reactancia) en Ω/km

    Args:
        data_type (str): Tipo de dato a consultar:
            - 'ampacidad'
            - 'factor_temp'
            - 'factor_agrupamiento'
            - 'reactancia_resistencia'
        **kwargs: Argumentos específicos según el tipo de consulta:
            - calibre (str): Calibre AWG del conductor
            - material (str): "Cobre" o "Aluminio"
            - temp_aislante (int): Temperatura del aislamiento en °C
            - temp_ambiente (int): Temperatura ambiente en °C
            - num_conductores (int): Número de conductores agrupados

    Returns:
        tuple: Resultado de la consulta según el tipo de dato:
            - Ampacidad: (ampacidad,)
            - Factores: (factor,)
            - Características: (resistencia, reactancia)
            - None: Si no se encuentra el dato

    Note:
        La función utiliza @lru_cache para almacenar en caché los resultados
        de las consultas más frecuentes, mejorando significativamente el
        rendimiento en cálculos repetitivos.
    """
    # Establecer conexión con la base de datos normativa
    conn = sqlite3.connect('database/normative_data.db')
    c = conn.cursor()
    
    # Seleccionar consulta según el tipo de dato solicitado
    if data_type == 'ampacidad':
        # Consulta de capacidad de conducción de corriente
        c.execute(
            'SELECT ampacidad FROM ampacidad_cables WHERE calibre_awg = ? AND material = ? AND temperatura_aislante = ?',
            (kwargs['calibre'], kwargs['material'], kwargs['temp_aislante'])
        )
    elif data_type == 'factor_temp':
        # Consulta de factor de corrección por temperatura
        c.execute(
            'SELECT factor FROM factores_correccion_temp WHERE temperatura_ambiente = ?',
            (kwargs['temp_ambiente'],)
        )
    elif data_type == 'factor_agrupamiento':
        # Consulta de factor de corrección por agrupamiento
        c.execute(
            'SELECT factor FROM factores_correccion_agrupamiento WHERE numero_conductores = ?',
            (kwargs['num_conductores'],)
        )
    elif data_type == 'reactancia_resistencia':
        # Consulta de características eléctricas del conductor
        c.execute(
            'SELECT resistencia_ohm_km, reactancia_ohm_km FROM reactancia_resistencia_cables WHERE calibre_awg = ?',
            (kwargs['calibre'],)
        )
    
    # Obtener resultado y cerrar conexión
    result = c.fetchone()
    conn.close()
    return result

def init_user_db(path_db):
    """Inicializa la base de datos de usuarios y registro de actividades.

    Esta función crea dos tablas principales:

    1. users: Almacena información de usuarios del sistema
       - id: Identificador único autoincremental
       - username: Nombre de usuario (único)
       - password: Contraseña hasheada
       - role: Rol del usuario (admin, user, etc.)

    2. logs: Registra actividades de los usuarios
       - id: Identificador único autoincremental
       - user_id: ID del usuario que realizó la acción
       - action: Descripción de la acción realizada
       - timestamp: Fecha y hora de la acción

    Args:
        path_db (str): Ruta absoluta al archivo de base de datos

    Note:
        - Las contraseñas se almacenan hasheadas por seguridad
        - Los logs mantienen referencia al usuario mediante foreign key
        - El timestamp se genera automáticamente
    """
    # Establecer conexión con la base de datos
    conn = sqlite3.connect(path_db)
    c = conn.cursor()

    # Crear tabla de usuarios con restricciones de seguridad
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único
            username TEXT UNIQUE NOT NULL,         -- Nombre de usuario único
            password TEXT NOT NULL,                -- Contraseña hasheada
            role TEXT NOT NULL                     -- Rol del usuario
        )
    ''')

    # Crear tabla de registro de actividades
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único
            user_id INTEGER,                       -- ID del usuario
            action TEXT NOT NULL,                  -- Acción realizada
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Fecha y hora
            FOREIGN KEY (user_id) REFERENCES users (id)   -- Referencia a users
        )
    ''')

    # Confirmar cambios y cerrar conexión
    conn.commit()
    conn.close()


def init_normative_db(path_db):
    """Inicializa la base de datos de normativas eléctricas.

    Crea cuatro tablas principales para almacenar datos normativos:
    1. ampacidad_cables: Capacidad de conducción de corriente
       - calibre_awg: Calibre del conductor (e.g., "14", "12", "1/0")
       - material: Material del conductor ("Cobre" o "Aluminio")
       - temperatura_aislante: Temperatura nominal del aislamiento (°C)
       - ampacidad: Corriente máxima permitida (Amperios)

    2. factores_correccion_temp: Ajustes por temperatura ambiente
       - temperatura_ambiente: Temperatura del entorno (°C)
       - factor: Coeficiente de corrección por temperatura

    3. factores_correccion_agrupamiento: Ajustes por cables agrupados
       - numero_conductores: Cantidad de conductores en la canalización
       - factor: Factor de reducción de capacidad

    4. reactancia_resistencia_cables: Propiedades eléctricas
       - calibre_awg: Calibre del conductor
       - resistencia_ohm_km: Resistencia por kilómetro (Ω/km)
       - reactancia_ohm_km: Reactancia por kilómetro (Ω/km)

    Args:
        path_db (str): Ruta absoluta al archivo de base de datos

    Note:
        - Los datos se basan en normas eléctricas vigentes
        - Todas las tablas se crean vacías para ser pobladas posteriormente
        - Las unidades siguen el sistema internacional (SI)
    """
    conn = sqlite3.connect(path_db)
    c = conn.cursor()

    # Tabla de capacidad de conducción de corriente
    c.execute('''
        CREATE TABLE IF NOT EXISTS ampacidad_cables (
            calibre_awg TEXT,              -- Calibre del conductor
            material TEXT,                 -- Material conductor (Cu/Al)
            temperatura_aislante INTEGER,  -- Temperatura nominal
            ampacidad REAL                 -- Corriente máxima (A)
        )
    ''')

    # Tabla de factores de corrección por temperatura
    c.execute('''
        CREATE TABLE IF NOT EXISTS factores_correccion_temp (
            temperatura_ambiente INTEGER,  -- Temperatura del entorno
            factor REAL                    -- Factor de corrección
        )
    ''')

    # Tabla de factores de corrección por agrupamiento
    c.execute('''
        CREATE TABLE IF NOT EXISTS factores_correccion_agrupamiento (
            numero_conductores INTEGER,    -- Cantidad de conductores
            factor REAL                    -- Factor de reducción
        )
    ''')

    # Tabla de características eléctricas de conductores
    c.execute('''
        CREATE TABLE IF NOT EXISTS reactancia_resistencia_cables (
            calibre_awg TEXT,             -- Calibre del conductor
            resistencia_ohm_km REAL,       -- Resistencia por km
            reactancia_ohm_km REAL         -- Reactancia por km
        )
    ''')

    # Confirmar cambios y cerrar conexión
    conn.commit()
    conn.close()
