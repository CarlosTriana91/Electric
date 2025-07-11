# create_admin.py
import sqlite3
import bcrypt
import os

# --- CONFIGURACIÓN ---
DB_FILE = os.path.join('database', 'users.db')
ADMIN_USERNAME = 'admin'
# Se recomienda usar una contraseña más segura y gestionarla con variables de entorno
ADMIN_PASSWORD = b'admin789' 

# 1) Conectarse a la BD de usuarios
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 2) Hashear la contraseña con bcrypt
hashed_password = bcrypt.hashpw(ADMIN_PASSWORD, bcrypt.gensalt())

# 3) Insertar o reemplazar el usuario 'admin' con rol 'Administrador'
# Usamos INSERT OR REPLACE para poder ejecutar el script varias veces sin errores
cursor.execute(
    """INSERT OR REPLACE INTO users (username, password, role) 
       VALUES (?, ?, ?)""",
    (ADMIN_USERNAME, hashed_password, 'Administrador')
)

# 4) Guardar y cerrar
conn.commit()
conn.close()

print(f"✅ Usuario '{ADMIN_USERNAME}' creado/actualizado con éxito.")
