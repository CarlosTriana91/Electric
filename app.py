# app.py
import os
from flask import Flask, session, redirect, url_for, render_template, request
from flask_babel import Babel
from modules.auth import auth_bp
from modules.admin import admin_bp
from modules.db_init import init_db

def create_app():
    """Crea y configura una instancia de la aplicación Flask."""
    app = Flask(__name__)
    
    # --- CONFIGURACIÓN DE LA APLICACIÓN ---
    app.secret_key = 'a_very_secret_key_that_is_not_random'
    app.config['USER_DB'] = os.path.join('database', 'users.db')
    app.config['CALC_DB'] = os.path.join('database', 'calculations.db')
    
    # --- CONFIGURACIÓN DE BABEL ---
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'
    app.config['LANGUAGES'] = {
        'en': 'English',
        'es': 'Español'
    }
    
    babel = Babel()

    def get_locale():
        if 'lang' in session:
            return session['lang']
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    
    babel.init_app(app, locale_selector=get_locale)

    # --- INICIALIZACIÓN DE LA BASE DE DATOS ---
    init_db(app)

    # --- REGISTRO DE BLUEPRINTS ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # --- RUTAS ---
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
        else:
            return render_template('dashboard.html', current_user=current_user)
            
    return app

# --- PUNTO DE ENTRADA ---
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)
