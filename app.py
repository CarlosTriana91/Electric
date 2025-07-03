# Importaciones necesarias para la aplicación
# Flask: Framework web para Python
# Módulos propios: auth, db_init, calculations, reporting, exports
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, send_from_directory
from flask_compress import Compress  # Para comprimir respuestas HTTP y mejorar el rendimiento
from datetime import timedelta

# Importación de módulos propios
from modules.auth import auth_bp  # Gestión de autenticación
from modules.db_init import init_user_db, init_normative_db  # Inicialización de bases de datos
from modules.calculations import select_cable, calculate_voltage_drop, dimension_channel  # Cálculos eléctricos
from modules.reporting import generate_pdf_report, generate_excel_report  # Generación de reportes
from modules.exports import export_for_revit  # Exportación a Revit

# Bibliotecas estándar
import os  # Operaciones del sistema de archivos
import pandas as pd  # Manipulación de datos
from datetime import datetime  # Manejo de fechas y horas

# Inicialización y configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Clave para sesiones y cookies - IMPORTANTE: Cambiar en producción

# Configuración de rutas de bases de datos
app.config['USER_DB'] = os.path.join('database', 'users.db')  # Base de datos de usuarios
app.config['NORM_DB'] = os.path.join('database', 'normative_data.db')  # Base de datos de normativas

# Activar compresión de respuestas HTTP para mejorar el rendimiento
Compress(app)

# Configuración de caché para archivos estáticos (CSS, JS, imágenes)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(days=7)  # Caché de 7 días

# Middleware para agregar headers de caché
@app.after_request
def add_header(response):
    """Agrega headers de control de caché a las respuestas HTTP"""
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'public, max-age=604800'  # Cache por 7 días
    return response

# Creación de estructura de directorios necesaria
for folder in ['uploads', 'reports']:  # Carpetas para archivos subidos y reportes generados
    if not os.path.exists(folder):
        os.makedirs(folder)

# Inicialización de bases de datos (solo si no existen)
if not os.path.exists(app.config['USER_DB']):
    init_user_db(app.config['USER_DB'])  # Crea la base de datos de usuarios
if not os.path.exists(app.config['NORM_DB']):
    init_normative_db(app.config['NORM_DB'])  # Crea la base de datos de normativas

# Registro del módulo de autenticación
app.register_blueprint(auth_bp, url_prefix='/auth')  # Todas las rutas de auth comenzarán con /auth

# Middleware de autenticación
@app.before_request
def check_auth():
    """Verifica que el usuario esté autenticado antes de acceder a rutas protegidas"""
    public_routes = ['auth.login', 'auth.logout', 'static']  # Rutas que no requieren autenticación
    if not any(request.endpoint.startswith(route) for route in public_routes):
        if 'user_id' not in session:  # Si no hay sesión activa
            return redirect(url_for('auth.login'))  # Redirige al login

# Rutas principales de la aplicación

@app.route('/')
def index():
    """Ruta raíz: Redirige al usuario a la página de login"""
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    """Dashboard principal:
    - Muestra lista de proyectos del usuario
    - Punto de entrada principal después del login
    TODO: Implementar obtención real de proyectos desde la base de datos
    """
    proyectos = [
        {   # Datos de ejemplo - reemplazar con datos reales de BD
            'id': 1,
            'nombre': 'Proyecto Demo',
            'usuario': session.get('username'),
            'fecha_creacion': '2024-01-01'
        }
    ]
    return render_template('dashboard.html', proyectos=proyectos)

@app.route('/proyecto/<int:proyecto_id>')
def proyecto(proyecto_id):
    """Vista detallada de un proyecto específico:
    - Muestra información detallada del proyecto
    - Permite acceder a funciones de cálculo y exportación
    
    Args:
        proyecto_id (int): Identificador único del proyecto
    
    TODO: Implementar obtención real de datos del proyecto desde la base de datos
    """
    proyecto = {   # Datos de ejemplo - reemplazar con datos reales de BD
        'id': proyecto_id,
        'nombre': f'Proyecto {proyecto_id}',
        'usuario': session.get('username'),
        'fecha_creacion': '2024-01-01'
    }
    return render_template('proyecto.html', proyecto=proyecto)

# Subir archivo Excel
@app.route('/proyecto/<int:proyecto_id>/upload', methods=['POST'])
def upload_excel(proyecto_id):
    if 'excel_file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('proyecto', proyecto_id=proyecto_id))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('proyecto', proyecto_id=proyecto_id))

    try:
        # Leer el archivo Excel
        df = pd.read_excel(file)
        
        # Verificar columnas requeridas
        required_columns = ['ID_Equipo', 'Descripcion', 'Potencia_HP', 
                          'Voltaje', 'Factor_Potencia', 'Longitud_m']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            flash(f'Faltan columnas requeridas: {", ".join(missing_columns)}', 'error')
            return redirect(url_for('proyecto', proyecto_id=proyecto_id))

        # Guardar el archivo
        filename = f'proyecto_{proyecto_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join('uploads', filename)
        df.to_excel(file_path, index=False)
        
        flash('Archivo subido exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'error')
    
    return redirect(url_for('proyecto', proyecto_id=proyecto_id))

# Cálculos eléctricos
@app.route('/proyecto/<int:proyecto_id>/calculate', methods=['POST'])
def run_calculation(proyecto_id):
    """Realiza los cálculos eléctricos para todos los equipos del proyecto.
    
    Proceso de cálculo:
    1. Valida los parámetros de entrada (temperatura, número de conductores, voltaje)
    2. Carga los datos del archivo Excel más reciente del proyecto
    3. Para cada equipo calcula:
       - Corriente nominal
       - Selección de calibre de cable
       - Caída de tensión
       - Dimensionamiento de canalización
    
    Args:
        proyecto_id (int): ID del proyecto a calcular
    
    Returns:
        redirect: Redirige a la vista del proyecto con resultados o mensajes de error
    """
    try:
        # Obtener y validar parámetros del formulario
        temp_amb = float(request.form['temp_amb'])  # Temperatura ambiente
        num_cond = int(request.form['num_cond'])   # Número de conductores
        voltaje = float(request.form['voltaje'])   # Voltaje del sistema
        
        # Validación de rangos según normas eléctricas
        if not (-20 <= temp_amb <= 50):
            raise ValueError('Temperatura fuera de rango (-20°C a 50°C)')
        if not (1 <= num_cond <= 20):
            raise ValueError('Número de conductores fuera de rango (1 a 20)')
        if not (110 <= voltaje <= 13800):
            raise ValueError('Voltaje fuera de rango (110V a 13800V)')
        
        # Buscar el archivo Excel más reciente del proyecto
        excel_files = [f for f in os.listdir('uploads') if f.startswith(f'proyecto_{proyecto_id}_')]
        if not excel_files:
            raise FileNotFoundError('No se encontró el archivo de datos del proyecto')
        
        latest_file = max(excel_files, key=lambda x: os.path.getctime(os.path.join('uploads', x)))
        df = pd.read_excel(os.path.join('uploads', latest_file))
        
        # Procesar cada equipo y realizar cálculos
        resultados = []
        for _, equipo in df.iterrows():
            # Cálculo de corriente nominal (I = P / (V * FP * √3))
            corriente = (equipo['Potencia_HP'] * 746) / (voltaje * equipo['Factor_Potencia'] * 1.732)
            
            # Selección de cable según corriente y temperatura
            calibre = select_cable(corriente, temp_amb)
            
            # Cálculo de caída de tensión considerando longitud
            caida_tension = calculate_voltage_drop(
                corriente, equipo['Longitud_m'], calibre, voltaje
            )
            
            # Dimensionamiento de canalización según NEC
            canalizacion = dimension_channel(calibre, num_cond)
            
            # Almacenar resultados del equipo
            resultados.append({
                'ID_Equipo': equipo['ID_Equipo'],
                'Descripcion': equipo['Descripcion'],
                'Corriente': corriente,
                'Calibre': calibre,
                'Caida_Tension': caida_tension,
                'Canalizacion': canalizacion
            })
        
        # Guardar resultados en la sesión para su posterior exportación
        session[f'resultados_{proyecto_id}'] = resultados
        flash('Cálculos completados exitosamente', 'success')
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
    except FileNotFoundError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error al realizar los cálculos: {str(e)}', 'error')
    
    return redirect(url_for('proyecto', proyecto_id=proyecto_id))

# Exportación de resultados en diferentes formatos
@app.route('/proyecto/<int:proyecto_id>/export/<format>')
def export_results(proyecto_id, format):
    """Exporta los resultados de los cálculos en diferentes formatos.
    
    Formatos soportados:
    - PDF: Reporte detallado con tablas y gráficos
    - Excel: Hoja de cálculo con todos los resultados
    - Revit: Archivo compatible con Autodesk Revit
    
    Args:
        proyecto_id (int): ID del proyecto
        format (str): Formato de exportación ('pdf', 'excel', 'revit')
    
    Returns:
        redirect: Redirige a la vista del proyecto con mensaje de éxito o error
    """
    # Obtener resultados almacenados en la sesión
    resultados = session.get(f'resultados_{proyecto_id}')
    if not resultados:
        flash('No hay resultados para exportar', 'error')
        return redirect(url_for('proyecto', proyecto_id=proyecto_id))
    
    try:
        # Seleccionar el tipo de exportación según el formato
        if format == 'pdf':
            file_path = generate_pdf_report(resultados, proyecto_id)  # Genera reporte PDF
        elif format == 'excel':
            file_path = generate_excel_report(resultados, proyecto_id)  # Genera hoja de cálculo
        elif format == 'revit':
            file_path = export_for_revit(resultados, proyecto_id)  # Genera archivo para Revit
        else:
            raise ValueError('Formato no soportado')
        
        # TODO: Implementar la descarga del archivo generado
        flash('Exportación completada exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'error')
    
    return redirect(url_for('proyecto', proyecto_id=proyecto_id))

if __name__ == '__main__':
    """Punto de entrada principal de la aplicación.
    
    Inicia el servidor de desarrollo de Flask con las siguientes características:
    - Modo debug activado para desarrollo
    - Recarga automática cuando se detectan cambios en el código
    - Mensajes detallados de error en caso de excepciones
    """
    app.run(debug=True)  # debug=True solo para desarrollo, cambiar a False en producción
