# app.py
import os
import sqlite3
from flask import Flask, session, redirect, url_for, render_template, request, g
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

from config import Config
from modules.auth import auth_bp
from modules.admin import admin_bp
from modules.db_init import init_user_db, init_db
from modules.plants import plants_bp
from modules.projects import projects_bp



def create_app():
    """Crea y configura una instancia de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['MAIN_DB'] = os.path.join('database', 'main_data.db')

    csrf = CSRFProtect()
    csrf.init_app(app)

    babel = Babel()

    def get_locale():
        if 'lang' in session:
            return session['lang']
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

    babel.init_app(app, locale_selector=get_locale)

    with app.app_context():
        # 1. Crear carpetas necesarias
        for folder in ['uploads', 'reports', 'database']:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # 2. Inicializar la base de datos de usuarios
        if not os.path.exists(app.config['USER_DB']):
            init_user_db(app.config['USER_DB'])
        
        # 3. Inicializar la base de datos de plantas
        if not os.path.exists(app.config['PLANTS_DB']):
            init_db(app.config['PLANTS_DB'], 'schemas/plants_schema.sql')

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(plants_bp)
    app.register_blueprint(projects_bp)

    @app.before_request
    def before_request():
        if request.method == 'POST':
            import logging
            logging.warning(f'Request form data in before_request: {request.form}')
        g.user_db = sqlite3.connect(app.config['USER_DB'])
        g.user_db.row_factory = sqlite3.Row
        g.plants_db = sqlite3.connect(app.config['PLANTS_DB'])
        g.plants_db.row_factory = sqlite3.Row

    @app.teardown_request
    def teardown_request(exception):
        user_db = getattr(g, 'user_db', None)
        if user_db is not None:
            user_db.close()
        plants_db = getattr(g, 'plants_db', None)
        if plants_db is not None:
            plants_db.close()

    @app.route('/change_language/<lang>')
    def change_language(lang):
        if lang in app.config['LANGUAGES']:
            session['lang'] = lang
        return redirect(request.referrer or url_for('index'))

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        current_user = {
            'username': session.get('username'),
            'role': session.get('role')
        }

        if session.get('role') == 'Administrador':
            return render_template('admin/dashboard.html', current_user=current_user)
        elif session.get('role') == 'Ingeniero':
            return render_template('ing/dashboard.html', current_user=current_user)
        else:
            return render_template('consultor/dashboard.html', current_user=current_user)

    return app

# --- PUNTO DE ENTRADA ---
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)
