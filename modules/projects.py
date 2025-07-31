# modules/projects.py

from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session, current_app)
import sqlite3
from functools import wraps

# Decorador para requerir rol de Ingeniero o Administrador
def engineer_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') not in ['Administrador', 'Ingeniero']:
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Crear el Blueprint para los proyectos
projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

def get_main_db_connection():
    """Conecta a la base de datos principal."""
    conn = sqlite3.connect(current_app.config['MAIN_DB'])
    conn.row_factory = sqlite3.Row
    return conn

@projects_bp.route('/', defaults={'planta_id': None}, methods=['GET'])
@projects_bp.route('/<int:planta_id>', methods=['GET', 'POST'])
@engineer_or_admin_required
def manage_projects(planta_id):
    """
    Muestra y gestiona los proyectos. Si no se especifica una planta,
    muestra una página para seleccionar una.
    """
    if planta_id is None:
        # Si no se proporciona planta_id, mostrar página de selección de planta
        conn = get_main_db_connection()
        plants = conn.execute('SELECT * FROM plants ORDER BY nombre').fetchall()
        conn.close()
        return render_template('select_plant_for_projects.html', plants=plants)

    # Lógica para crear un nuevo proyecto para esta planta
    if request.method == 'POST':
        nombre_proyecto = request.form['nombre']
        if not nombre_proyecto:
            flash('El nombre del proyecto es obligatorio.', 'warning')
        else:
            try:
                conn = get_main_db_connection()
                conn.execute(
                    'INSERT INTO projects (nombre, planta_id) VALUES (?, ?)',
                    (nombre_proyecto, planta_id)
                )
                conn.commit()
                flash(f"Proyecto '{nombre_proyecto}' creado exitosamente.", 'success')
            except Exception as e:
                flash(f'Error al crear el proyecto: {e}', 'danger')
            finally:
                if conn:
                    conn.close()
        return redirect(url_for('projects.manage_projects', planta_id=planta_id))

    # Lógica para mostrar la lista de proyectos de la planta
    conn = get_main_db_connection()
    # Obtener datos de la planta para mostrar su nombre
    planta = conn.execute('SELECT * FROM plants WHERE id = ?', (planta_id,)).fetchone()
    # Obtener la lista de proyectos de esa planta
    projects = conn.execute('SELECT * FROM projects WHERE planta_id = ? ORDER BY nombre', (planta_id,)).fetchall()
    conn.close()

    if not planta:
        flash('La planta especificada no existe.', 'danger')
        return redirect(url_for('plants.manage_plants'))

    return render_template('projects.html', projects=projects, planta=planta, template_name='projects.html')

@projects_bp.route('/edit/<int:id>', methods=['POST'])
@engineer_or_admin_required
def edit_project(id):
    """Maneja la edición de un proyecto existente."""
    nombre_proyecto = request.form['nombre']
    planta_id = request.form['planta_id'] # Necesitamos saber a qué planta volver
    if not nombre_proyecto:
        flash('El nombre del proyecto es obligatorio.', 'warning')
        return redirect(url_for('projects.manage_projects', planta_id=planta_id))
    try:
        conn = get_main_db_connection()
        conn.execute('UPDATE projects SET nombre = ? WHERE id = ?', (nombre_proyecto, id))
        conn.commit()
        flash('Proyecto actualizado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al editar el proyecto: {e}', 'danger')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('projects.manage_projects', planta_id=planta_id))

@projects_bp.route('/delete/<int:id>', methods=['POST'])
@engineer_or_admin_required
def delete_project(id):
    """Maneja la eliminación de un proyecto."""
    planta_id = request.form['planta_id'] # Necesitamos saber a qué planta volver
    try:
        conn = get_main_db_connection()
        conn.execute('DELETE FROM projects WHERE id = ?', (id,))
        conn.commit()
        flash('Proyecto eliminado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar el proyecto: {e}', 'danger')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('projects.manage_projects', planta_id=planta_id))

