import sqlite3

def migrate():
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()

    try:
        # Añadir la columna de correo electrónico si no existe
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
        print('Columna "email" añadida a la tabla de usuarios.')
    except sqlite3.OperationalError as e:
        # La columna ya existe, lo cual es esperado en ejecuciones posteriores
        if 'duplicate column name' in str(e):
            print('La columna "email" ya existe en la tabla de usuarios.')
        else:
            raise e

    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()