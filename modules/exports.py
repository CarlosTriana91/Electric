import csv
from datetime import datetime
import os

def export_for_revit(resultados, proyecto_id):
    """Exporta los resultados a un archivo CSV compatible con Revit/Eplan."""
    # Crear directorio reports si no existe
    if not os.path.exists('reports'):
        os.makedirs('reports')
    
    # Nombre del archivo
    filename = f'reports/proyecto_{proyecto_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}_revit.csv'
    
    # Encabezados para Revit
    headers = [
        'ID_Equipo',
        'Descripcion',
        'Corriente_A',
        'Calibre_AWG',
        'Caida_Tension_Pct',
        'Canalizacion_in',
        'Estado',
        'Familia_Revit',
        'Tipo_Revit'
    ]
    
    # Mapeo de calibres a familias Revit
    familia_por_calibre = {
        '14 AWG': 'Cable_THHN_14',
        '12 AWG': 'Cable_THHN_12',
        '10 AWG': 'Cable_THHN_10',
        '8 AWG': 'Cable_THHN_8',
        '6 AWG': 'Cable_THHN_6',
        '4 AWG': 'Cable_THHN_4',
        '2 AWG': 'Cable_THHN_2',
        '1/0': 'Cable_THHN_1/0',
        '2/0': 'Cable_THHN_2/0',
        '3/0': 'Cable_THHN_3/0',
        '4/0': 'Cable_THHN_4/0'
    }
    
    # Mapeo de canalizaciones a familias Revit
    familia_canalizacion = {
        '1"': 'Conduit_EMT_1',
        '1-1/4"': 'Conduit_EMT_1-1/4',
        '1-1/2"': 'Conduit_EMT_1-1/2',
        '2"': 'Conduit_EMT_2',
        '2-1/2"': 'Conduit_EMT_2-1/2',
        '3"': 'Conduit_EMT_3',
        '4"': 'Conduit_EMT_4'
    }
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for r in resultados:
            estado = 'OK' if r['Caida_Tension'] <= 3 else 'Revisar' if r['Caida_Tension'] <= 5 else 'Fuera de rango'
            
            # Determinar familia y tipo Revit para el cable
            familia_cable = familia_por_calibre.get(r['Calibre'], 'Cable_THHN_Generico')
            
            # Determinar familia y tipo Revit para la canalización
            familia_conduit = familia_canalizacion.get(r['Canalizacion'], 'Conduit_EMT_Generico')
            
            writer.writerow({
                'ID_Equipo': r['ID_Equipo'],
                'Descripcion': r['Descripcion'],
                'Corriente_A': f"{r['Corriente']:.2f}",
                'Calibre_AWG': r['Calibre'],
                'Caida_Tension_Pct': f"{r['Caida_Tension']:.2f}",
                'Canalizacion_in': r['Canalizacion'],
                'Estado': estado,
                'Familia_Revit': f"{familia_cable}|{familia_conduit}",
                'Tipo_Revit': 'THHN|EMT'
            })
    
    return filename
