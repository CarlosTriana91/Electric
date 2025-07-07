"""Módulo de Autenticación y Control de Acceso

Este módulo maneja toda la lógica relacionada con la autenticación de usuarios,
incluyendo login, logout y gestión de sesiones. Utiliza SQLite para almacenar
los datos de usuarios y implementa medidas de seguridad como el hash de contraseñas.

Características principales:
- Autenticación basada en formularios
- Almacenamiento seguro de contraseñas con hash
- Gestión de sesiones de usuario
- Control de acceso basado en roles
"""

from flask import (
    Blueprint,        # Para crear módulos independientes de rutas
    render_template,  # Para renderizar vistas HTML
    request,          # Para acceder a datos de peticiones HTTP
    redirect,         # Para redireccionar a otras rutas
    url_for,          # Para generar URLs dinámicas
    session,          # Para manejar datos de sesión del usuario
    flash,            # Para mensajes flash entre peticiones
    current_app       # Para acceder a la configuración global
)
import sqlite3  # Base de datos ligera para almacenar usuarios
import bcrypt

# Blueprint de autenticación
auth_bp = Blueprint('auth', __name__,template_folder='../../templates/auth', url_prefix='/auth') # Ruta correcta a los templates


def get_db():
   """Establece conexión con la base de datos de usuarios."""
   conn = sqlite3.connect(current_app.config['USER_DB'])
   conn.row_factory = sqlite3.Row
   return conn


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el proceso de autenticación de usuarios.
    
    GET: Muestra el formulario de login
    POST: Procesa los datos del formulario y autentica al usuario
    
    El proceso de autenticación incluye:
    1. Validación de credenciales contra la base de datos
    2. Creación de sesión para usuarios autenticados
    3. Redirección según el resultado de la autenticación
    
    Returns:
        GET: Plantilla del formulario de login
        POST: Redirección al dashboard o nuevamente al login si falla
    """
    if request.method == 'POST':
        # Obtener credenciales del formulario
        username = request.form['username'] # Nombre de usuario
        # Es importante codificar la contraseña que viene del formulario
        password = request.form['password'].encode('utf-8')
       
        # Verificar credenciales en la base de datos
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()


        # Validar credenciales y crear sesión
         # Se usa bcrypt.checkpw para ser consistente con la creación de usuarios
        # La contraseña de la BD (user['password']) ya está en bytes.
        if user and bcrypt.checkpw(password, user['password']):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
            
    return render_template('login.html', template_name='auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario actual, conservando el idioma.

    - Guarda el idioma actual de la sesión.
    - Limpia todos los demás datos de la sesión.
    - Restaura el idioma en la nueva sesión.
    - Redirige al usuario a la página de login.

    Returns:
        redirect: Redirección a la página de login.
    """
    # Guarda el idioma actual antes de limpiar la sesión
    lang = session.get('lang', None)

    # Limpia la sesión para eliminar los datos del usuario
    session.clear()

    # Restaura el idioma en la nueva sesión
    if lang:
        session['lang'] = lang
        
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))
