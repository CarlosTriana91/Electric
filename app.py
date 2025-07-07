# Importaciones necesarias para la aplicación
# 1. INICIALIZACIÓN DE LA APLICACIÓN
from flask import (Flask, render_template, redirect, url_for, request, flash, session, jsonify, send_from_directory, g)
from flask_babel import Babel, gettext as _
from flask_compress import Compress
from datetime import timedelta
from jinja2 import select_autoescape

# Importación de módulos propios
from modules.auth import auth_bp
from modules.db_init import init_user_db, init_normative_db
from modules.calculations import select_cable, calculate_voltage_drop, dimension_channel
from modules.reporting import generate_pdf_report, generate_excel_report
from modules.exports import export_for_revit
from modules.admin import admin_bp

# Bibliotecas estándar
import os
import pandas as pd
from datetime import datetime

# Inicialización y configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'


# 2. CONFIGURACIÓN CENTRALIZADA

# Configuración de Jinja2 y Babel
app.jinja_env.add_extension('jinja2.ext.i18n')
app.jinja_env.autoescape = select_autoescape(['html', 'xml'])

# Configuración de Babel (DEBE estar antes de la inicialización de Babel)
app.config.update(
    BABEL_DEFAULT_LOCALE='es',
    BABEL_TRANSLATION_DIRECTORIES='translations',
    LANGUAGES={'en': 'English', 'es': 'Español'},
    BABEL_SUPPORTED_LOCALES=['es', 'en']
)

# Selector de idioma
def get_locale():
    # Prioriza el idioma de la sesión, si es válido
    if 'lang' in session and session['lang'] in app.config['BABEL_SUPPORTED_LOCALES']:
        return session['lang']
    # Si no, intenta con el mejor match del navegador
    best_match = request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])
    if best_match:
        return best_match
    # Finalmente, usa el idioma por defecto
    return app.config['BABEL_DEFAULT_LOCALE']

# Configuración de rutas de bases de datos
app.config['USER_DB'] = os.path.join('database', 'users.db')
app.config['NORM_DB'] = os.path.join('database', 'normative_data.db')

# Configuración de caché para archivos estáticos
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(days=7)

# 3. INICIALIZACIÓN DE EXTENSIONES
# Inicialización de Babel
babel = Babel(app, locale_selector=get_locale)
Compress(app) # Activar compresión de respuestas HTTP

# 4. REGISTRO DE BLUEPRINTS
# Registro del módulo de autenticación
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# 5. MIDDLEWARE Y HANDLERS GLOBALES


# Middleware para cada solicitud: establece idioma y verifica autenticación
@app.before_request
def before_request_handler():
    # 1. Establecer el idioma para la solicitud actual
    g.locale = get_locale()
    print(f"[LOCALE] g.locale set to: {g.locale}")

    # 2. Verificar autenticación en rutas protegidas
    public_routes = ['auth.login', 'auth.logout', 'static', 'change_language']
    if request.endpoint and not any(request.endpoint.startswith(route) for route in public_routes):
        if 'user_id' not in session:
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'public, max-age=604800'
    return response

# 6. RUTAS PRINCIPALES

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
     return redirect(url_for('auth.login'))
    proyectos = [
        {
            'id': 1,
            'nombre': 'Proyecto Demo',
            'usuario': session.get('username'),
            'fecha_creacion': '2024-01-01'
        }
    ]
    return render_template('dashboard.html', proyectos=proyectos, template_name='dashboard.html')

@app.route('/proyecto/<int:proyecto_id>')
def proyecto(proyecto_id):
    proyecto = {
        'id': proyecto_id,
        'nombre': f'Proyecto {proyecto_id}',
        'usuario': session.get('username'),
        'fecha_creacion': '2024-01-01'
    }
    return render_template('proyecto.html', proyecto=proyecto,template_name='proyecto.html')

# Ruta para cambiar el idioma
@app.route('/change_language/<lang>')
def change_language(lang):
    print(f"Changing language to: {lang}")
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['lang'] = lang
        print(f"Language set in session: {session['lang']}")
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('dashboard'))
    print(f"Invalid language requested: {lang}")
    return redirect(url_for('dashboard'))


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


# 7. INICIALIZACIÓN DE LA APP Y DATOS
# Se añade el bloque with app.app_context()
with app.app_context():
    # Este código ahora se ejecuta en un entorno seguro.
    for folder in ['uploads', 'reports', 'database']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    if not os.path.exists(app.config['USER_DB']):
        init_user_db(app.config['USER_DB'])
    if not os.path.exists(app.config['NORM_DB']):
        init_normative_db(app.config['NORM_DB'])
        

if __name__ == '__main__':
    app.run(debug=True)
