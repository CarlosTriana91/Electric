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
from werkzeug.security import (
    generate_password_hash,  # Genera hash seguro de contraseñas
    check_password_hash      # Verifica contraseñas contra su hash
)

# Blueprint de autenticación
auth_bp = Blueprint('auth', __name__)

def get_db():
    """Establece conexión con la base de datos de usuarios.
    
    Returns:
        sqlite3.Connection: Conexión a la base de datos users.db
    
    Note:
        Utiliza la configuración global de la aplicación para la ruta de la BD
    """
    return sqlite3.connect(current_app.config['USER_DB'])

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
        user = request.form['username']  # Nombre de usuario
        pw   = request.form['password']  # Contraseña sin procesar

        # Verificar credenciales en la base de datos
        conn = get_db()
        c = conn.cursor()
        c.execute(
            'SELECT password_hash, role FROM users WHERE username = ?',
            (user,)  # Previene inyección SQL usando parámetros
        )
        row = c.fetchone()
        conn.close()

        # Validar credenciales y crear sesión
        if row and check_password_hash(row[0], pw):
            # Establecer datos de sesión
            session['username'] = user    # Identificador del usuario
            session['role']     = row[1]  # Rol para control de acceso
            return redirect(url_for('dashboard'))

        # Notificar error de autenticación
        flash('Usuario o contraseña incorrectos', 'danger')

    # Mostrar formulario de login
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario actual.
    
    - Elimina todos los datos de la sesión actual
    - Redirige al usuario a la página de login
    
    Returns:
        redirect: Redirige al usuario a la página de login
    """
    session.clear()  # Elimina todos los datos de sesión
    return redirect(url_for('auth.login'))
