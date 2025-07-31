# modules/plants.py

from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session, g)
import sqlite3
import logging
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

# Crear el Blueprint para las plantas
plants_bp = Blueprint('plants', __name__, url_prefix='/plants')



@plants_bp.route('/', methods=['GET', 'POST'])
@engineer_or_admin_required
def manage_plants():
    """Muestra la lista de plantas y maneja la creación de nuevas plantas."""
    if request.method == 'POST':
        logging.warning(f'Request form data: {request.form}')
        # Lógica para crear una nueva planta
        try:
            elevacion = request.form.get('elevacion')
            humedad = request.form.get('humedad')

            g.plants_db.execute(
                'INSERT INTO plants (nombre, cliente, sigla, pais, elevacion, humedad, medium_voltage, low_voltage, control_voltage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (request.form['nombre'], request.form['cliente'], request.form['sigla'], 
                 request.form['pais'], elevacion if elevacion else None, humedad if humedad else None,
                 request.form.get('medium_voltage'), request.form.get('low_voltage'), request.form.get('control_voltage'))
            )
            g.plants_db.commit()
            flash(f"Planta '{request.form['nombre']}' creada exitosamente.", 'success')
        except sqlite3.IntegrityError:
            flash('Ya existe una planta con ese nombre.', 'danger')
        except Exception as e:
            flash(f'Error al crear la planta: {e}', 'danger')
        return redirect(url_for('plants.manage_plants'))

    # Lógica para mostrar la lista de plantas
    plants = g.plants_db.execute('SELECT * FROM plants ORDER BY nombre').fetchall()
    return render_template('plants.html', plants=plants, template_name='plants.html')

@plants_bp.route('/edit/<int:id>', methods=['POST'])
@engineer_or_admin_required
def edit_plant(id):
    """Maneja la edición de una planta existente."""
    try:
        elevacion = request.form.get('elevacion')
        humedad = request.form.get('humedad')
        g.plants_db.execute(
            'UPDATE plants SET nombre=?, cliente=?, sigla=?, pais=?, elevacion=?, humedad=?, medium_voltage=?, low_voltage=?, control_voltage=? WHERE id=?',
            (request.form['nombre'], request.form['cliente'], request.form['sigla'],
             request.form['pais'], elevacion if elevacion else None, humedad if humedad else None, 
             request.form.get('medium_voltage'), request.form.get('low_voltage'), request.form.get('control_voltage'), id)
        )
        g.plants_db.commit()
        flash('Planta actualizada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al editar la planta: {e}', 'danger')
    return redirect(url_for('plants.manage_plants'))

@plants_bp.route('/delete/<int:id>', methods=['POST'])
@engineer_or_admin_required
def delete_plant(id):
    """Maneja la eliminación de una planta."""
    try:
        g.plants_db.execute('DELETE FROM plants WHERE id = ?', (id,))
        g.plants_db.commit()
        flash('Planta eliminada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar la planta: {e}', 'danger')
    return redirect(url_for('plants.manage_plants'))