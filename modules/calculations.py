import sqlite3
import math

from flask import current_app

def get_db_connection():
    """Establece conexión con la base de datos normativa."""
    # Usar la configuración de la app para obtener la ruta de la BD
    # Esto hace que el módulo sea más reutilizable y menos propenso a errores de ruta
    db_path = current_app.config['NORM_DB']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def select_cable(corriente, temperatura):
    """Selecciona el calibre del cable basado en la corriente y temperatura."""
    conn = get_db_connection()
    try:
        # Obtener factor de corrección por temperatura
        cursor = conn.execute(
            'SELECT factor FROM factores_correccion_temp WHERE temp_min <= ? AND temp_max >= ?',
            (temperatura, temperatura)
        )
        factor_temp = cursor.fetchone()
        if not factor_temp:
            raise ValueError(f'Temperatura {temperatura}°C fuera de rango')
        
        # Ajustar corriente por factor de temperatura
        corriente_ajustada = corriente / factor_temp['factor']
        
        # Seleccionar calibre basado en ampacidad
        cursor = conn.execute(
            'SELECT calibre FROM ampacidad_cables WHERE ampacidad >= ? ORDER BY ampacidad ASC LIMIT 1',
            (corriente_ajustada,)
        )
        resultado = cursor.fetchone()
        if not resultado:
            raise ValueError(f'Corriente {corriente_ajustada}A excede límites de tabla')
        
        return resultado['calibre']
        
    finally:
        conn.close()

def calculate_voltage_drop(corriente, longitud, calibre, voltaje_sistema):
    """Calcula la caída de tensión en porcentaje."""
    conn = get_db_connection()
    try:
        # Obtener resistencia y reactancia del cable
        cursor = conn.execute(
            'SELECT resistencia, reactancia FROM reactancia_resistencia_cables WHERE calibre = ?',
            (calibre,)
        )
        cable_data = cursor.fetchone()
        if not cable_data:
            raise ValueError(f'Calibre {calibre} no encontrado en tabla')
        
        # Calcular caída de tensión
        r = cable_data['resistencia']
        x = cable_data['reactancia']
        z = math.sqrt(r*r + x*x)  # impedancia
        
        # Fórmula para sistemas trifásicos
        caida_tension = (math.sqrt(3) * corriente * z * longitud) / (voltaje_sistema * 10)
        
        return caida_tension
        
    finally:
        conn.close()

def dimension_channel(calibre, num_conductores):
    """Dimensiona la canalización basado en el calibre y número de conductores."""
    # Área por calibre (mm²)
    areas = {
        '14 AWG': 2.08,
        '12 AWG': 3.31,
        '10 AWG': 5.26,
        '8 AWG': 8.37,
        '6 AWG': 13.3,
        '4 AWG': 21.2,
        '2 AWG': 33.6,
        '1/0': 53.5,
        '2/0': 67.4,
        '3/0': 85.0,
        '4/0': 107.2
    }
    
    if calibre not in areas:
        raise ValueError(f'Calibre {calibre} no soportado')
    
    # Área total requerida
    area_total = areas[calibre] * num_conductores
    
    # Factor de relleno (40% para más de 2 conductores)
    factor_relleno = 0.4
    area_canal = area_total / factor_relleno
    
    # Seleccionar tubería
    if area_canal <= 850:  # 1" = 853 mm²
        return '1"'
    elif area_canal <= 1320:  # 1-1/4" = 1,318 mm²
        return '1-1/4"'
    elif area_canal <= 2280:  # 1-1/2" = 2,280 mm²
        return '1-1/2"'
    elif area_canal <= 3810:  # 2" = 3,813 mm²
        return '2"'
    elif area_canal <= 6190:  # 2-1/2" = 6,187 mm²
        return '2-1/2"'
    elif area_canal <= 9630:  # 3" = 9,621 mm²
        return '3"'
    else:
        return '4"'  # 4" = 15,208 mm²
