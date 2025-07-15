# modules/admin.py

# modules/admin.py

print("Importing admin module...")
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session, g)
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

    if request.method == 'POST':
        user_id = request.form.get('user_id')

        if user_id:  # Actualizar rol de usuario existente
            new_role = request.form.get('role')
            if new_role:
                try:
                    g.user_db.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
                    g.user_db.commit()
                    flash('Rol de usuario actualizado exitosamente.', 'success')
                except Exception as e:
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
                    g.user_db.execute('INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                                 (username, hashed_password, role, email))
                    g.user_db.commit()
                    flash(f'Usuario "{username}" creado exitosamente.', 'success')
                except Exception as e:
                    flash(f'El nombre de usuario "{username}" o el correo "{email}" ya existen.', 'danger')
        
        return redirect(url_for('admin.manage_users'))

    # Lógica para GET (mostrar usuarios con ordenación)
    sort_by = request.args.get('sort_by', 'username') # Ordenar por nombre de usuario por defecto
    if sort_by not in ['username', 'role', 'email']:
        sort_by = 'username'

    users = g.user_db.execute(f'SELECT id, username, role, email FROM users ORDER BY {sort_by}').fetchall()
    
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
        g.user_db.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', (new_username, new_email, user_id))
        g.user_db.commit()
        flash('Usuario actualizado exitosamente.', 'success')
    except Exception as e:
        flash(f'El nombre de usuario "{new_username}" o el correo "{new_email}" ya existen.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """
    Ruta para eliminar un usuario.
    """
    try:
        g.user_db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        g.user_db.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar el usuario: {e}', 'danger')
    return redirect(url_for('admin.manage_users'))
