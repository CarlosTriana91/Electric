# modules/admin.py

print("Importing admin module...")
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session)
import sqlite3
import bcrypt
from functools import wraps

# Crear un Blueprint para las rutas de administración
# Esto nos permite organizar las rutas de admin en un solo lugar.
import os

 # Todas las rutas aquí empezarán con /admin

def admin_required(f):
    """
    Decorador personalizado para asegurar que solo los administradores
    puedan acceder a estas rutas.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'Administrador':
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Funciones de base de datos ---
from flask import current_app

def get_user_db_connection():
    """Función auxiliar para conectar a la base de datos de usuarios."""
    db_path = current_app.config['USER_DB']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# --- Rutas del panel de administración ---

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    """
    Página principal para la gestión de usuarios.
    - Muestra la lista de todos los usuarios.
    - Procesa el formulario para crear o actualizar un usuario.
    """
    conn = get_user_db_connection()

    if request.method == 'POST':
        user_id = request.form.get('user_id')

        if user_id:  # Actualizar rol de usuario existente
            new_role = request.form.get('role')
            if new_role:
                try:
                    conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
                    conn.commit()
                    flash('Rol de usuario actualizado exitosamente.', 'success')
                except sqlite3.Error as e:
                    flash(f'Error al actualizar el rol del usuario: {e}', 'danger')
            else:
                flash('No se proporcionó un nuevo rol.', 'warning')

        else:  # Crear nuevo usuario
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role')
            email = request.form.get('email', '').strip()

            if not username or not password or not role or not email:
                flash('Todos los campos son obligatorios y no pueden estar vacíos.', 'warning')
            else:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                try:
                    conn.execute('INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                                 (username, hashed_password, role, email))
                    conn.commit()
                    flash(f'Usuario "{username}" creado exitosamente.', 'success')
                except sqlite3.IntegrityError:
                    flash(f'El nombre de usuario "{username}" o el correo "{email}" ya existen.', 'danger')
        
        conn.close()
        return redirect(url_for('admin.manage_users'))

    # Lógica para GET (mostrar usuarios con ordenación)
    sort_by = request.args.get('sort_by', 'username') # Ordenar por nombre de usuario por defecto
    if sort_by not in ['username', 'role', 'email']:
        sort_by = 'username'

    users = conn.execute(f'SELECT id, username, role, email FROM users ORDER BY {sort_by}').fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    """
    Ruta para editar el nombre y correo de un usuario.
    """
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip()

    if not new_username or not new_email:
        flash('El nombre de usuario y el correo no pueden estar vacíos.', 'warning')
        return redirect(url_for('admin.manage_users'))

    try:
        conn = get_user_db_connection()
        conn.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', (new_username, new_email, user_id))
        conn.commit()
        conn.close()
        flash('Usuario actualizado exitosamente.', 'success')
    except sqlite3.IntegrityError:
        flash(f'El nombre de usuario "{new_username}" o el correo "{new_email}" ya existen.', 'danger')
    except sqlite3.Error as e:
        flash(f'Error al actualizar el usuario: {e}', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """
    Ruta para eliminar un usuario.
    """
    try:
        conn = get_user_db_connection()
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('Usuario eliminado exitosamente.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al eliminar el usuario: {e}', 'danger')
    return redirect(url_for('admin.manage_users'))
