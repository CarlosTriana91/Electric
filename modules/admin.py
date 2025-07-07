# modules/admin.py

from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session)
import sqlite3
import bcrypt
from functools import wraps

# Crear un Blueprint para las rutas de administración
# Esto nos permite organizar las rutas de admin en un solo lugar.
admin_bp = Blueprint('admin', __name__,
                    template_folder='../templates/admin', # Le decimos dónde buscar sus templates
                    url_prefix='/admin') # Todas las rutas aquí empezarán con /admin

# --- Decorador de seguridad para proteger las rutas de admin ---
from functools import wraps

def admin_required(f):
    """
    Decorador personalizado para asegurar que solo los administradores
    puedan acceder a estas rutas.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'Administrador':
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Funciones de base de datos ---
def get_user_db_connection():
    """Función auxiliar para conectar a la base de datos de usuarios."""
    conn = sqlite3.connect('database/users.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Rutas del panel de administración ---

@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    """
    Página principal para la gestión de usuarios.
    - Muestra la lista de todos los usuarios.
    - Procesa el formulario para crear un nuevo usuario.
    """
    # Si el método es POST, significa que se está enviando el formulario para crear un usuario
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        role = request.form['role']

        # Validaciones básicas
        if not username or not password or not role:
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('admin.manage_users'))

        # Hashear la contraseña para almacenarla de forma segura
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            conn = get_user_db_connection()
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, hashed_password, role))
            conn.commit()
            conn.close()
            flash(f'Usuario "{username}" creado exitosamente.', 'success')
        except sqlite3.IntegrityError:
            flash(f'El nombre de usuario "{username}" ya existe.', 'danger')
        
        return redirect(url_for('admin.manage_users'))

    # Si el método es GET, simplemente muestra la página con la lista de usuarios
    conn = get_user_db_connection()
    users = conn.execute('SELECT id, username, role FROM users ORDER BY username').fetchall()
    conn.close()
    
    return render_template('users.html', users=users, template_name='admin/users.html')
