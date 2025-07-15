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
    Blueprint, render_template, request, redirect, url_for, session, flash, g
)
import bcrypt
from forms import LoginForm

# Blueprint de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data.encode('utf-8')

        user = g.user_db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and bcrypt.checkpw(password, user['password']):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            print(f"DEBUG: Datos de sesión guardados -> {session}")
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html', form=form)

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
