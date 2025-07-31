# modules/admin.py

from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session, g)
import bcrypt
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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

@admin_bp.route('/users', methods=['GET'])
@admin_required
def manage_users():
    """
    Muestra la lista de todos los usuarios con opción de ordenación.
    """
    sort_by = request.args.get('sort_by', 'username')
    if sort_by not in ['username', 'role', 'email']:
        sort_by = 'username'

    users = g.user_db.execute(f'SELECT id, username, role, email FROM users ORDER BY {sort_by}').fetchall()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    """
    Crea un nuevo usuario.
    """
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role')
    email = request.form.get('email', '').strip()

    if not all([username, password, role, email]):
        flash('Todos los campos son obligatorios.', 'warning')
    else:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            g.user_db.execute('INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                         (username, hashed_password, role, email))
            g.user_db.commit()
            flash(f'Usuario "{username}" creado exitosamente.', 'success')
        except g.user_db.IntegrityError:
            flash(f'El nombre de usuario "{username}" o el correo "{email}" ya existen.', 'danger')
        except Exception as e:
            flash(f'Error al crear el usuario: {e}', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    """
    Edita el nombre de usuario y el correo electrónico de un usuario.
    """
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip()

    if not new_username or not new_email:
        flash('El nombre de usuario y el correo no pueden estar vacíos.', 'warning')
    else:
        try:
            g.user_db.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', (new_username, new_email, user_id))
            g.user_db.commit()
            flash('Usuario actualizado exitosamente.', 'success')
        except g.user_db.IntegrityError:
            flash(f'El nombre de usuario "{new_username}" o el correo "{new_email}" ya existen.', 'danger')
        except Exception as e:
            flash(f'Error al actualizar el usuario: {e}', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/update_role', methods=['POST'])
@admin_required
def update_user_role(user_id):
    """
    Actualiza el rol de un usuario.
    """
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
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """
    Elimina un usuario.
    """
    try:
        g.user_db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        g.user_db.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar el usuario: {e}', 'danger')
    return redirect(url_for('admin.manage_users'))
