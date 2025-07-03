# create_admin.py
import sqlite3
from werkzeug.security import generate_password_hash

# 1) Conectarse a la BD de usuarios
conn = sqlite3.connect('database/users.db')
c = conn.cursor()

# 2) Generar el hash de la contraseña
pw_hash = generate_password_hash('Admin123')  # Cámbiala si quieres otra

# 3) Insertar el usuario 'admin' con rol 'Administrador'
c.execute(
    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
    ('admin', pw_hash, 'Administrador')
)

# 4) Guardar y cerrar
conn.commit()
conn.close()

print("✅ Usuario 'admin' creado con contraseña 'Admin123'")
