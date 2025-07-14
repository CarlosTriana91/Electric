# extract_messages.py (Versión Final y Corregida)

import os
from babel.messages.extract import extract
from babel.messages.pofile import Catalog

# 1. Creamos un catálogo de traducción vacío.
catalog = Catalog(
    project='Mi Aplicación Eléctrica',
    version='1.0',
    charset='UTF-8'
)

# 2. Definimos las carpetas que queremos escanear.
scan_dirs = ['.', 'modules', 'templates']

# --- LA CORRECCIÓN CLAVE ---
# 3. Definimos las palabras clave como un DICCIONARIO, no como un string.
#    Esto soluciona el error "AttributeError: 'str' object has no attribute 'keys'".
keywords = {'_': None, 'gettext': None}

print("Iniciando escaneo de archivos...")

# 4. Recorremos cada carpeta y cada archivo.
for dirname in scan_dirs:
    for dirpath, _, filenames in os.walk(dirname):
        for filename in filenames:
            # Solo procesamos archivos Python y HTML.
            if filename.endswith(('.py', '.html')):
                filepath = os.path.join(dirpath, filename)
                print(f"  -> Escaneando: {filepath}")

                # Usamos el método de extracción correcto para cada tipo de archivo.
                method = 'python' if filename.endswith('.py') else 'jinja2'

                with open(filepath, 'rb') as f:
                    # Extraemos los mensajes del archivo, pasando el diccionario de keywords.
                    messages = extract(method, f, keywords=keywords)
                    for lineno, message, comments, context in messages:
                        # Añadimos cada mensaje encontrado al catálogo.
                        catalog.add(message, None, [(filepath, lineno)], auto_comments=comments)

# 5. Escribimos el catálogo completo al archivo .pot.
pot_file_path = 'messages.pot'
print(f"\nEscribiendo {len(catalog)} mensajes en '{pot_file_path}'...")
with open(pot_file_path, 'wb') as potfile:
    from babel.messages.pofile import write_po
    write_po(potfile, catalog)

print("¡Extracción completada exitosamente!")