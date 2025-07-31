import sqlite3

def migrate():
    # Migrate users table
    try:
        conn_users = sqlite3.connect('database/users.db')
        cursor_users = conn_users.cursor()
        try:
            cursor_users.execute('ALTER TABLE users ADD COLUMN email TEXT')
            print('Columna "email" añadida a la tabla de usuarios.')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print('La columna "email" ya existe en la tabla de usuarios.')
            else:
                raise e
        conn_users.commit()
    except sqlite3.Error as e:
        print(f"Error with users.db: {e}")
    finally:
        if conn_users:
            conn_users.close()

    # Migrate plants table
    try:
        conn_plants = sqlite3.connect('database/plants.db')
        cursor_plants = conn_plants.cursor()
        
        # Check and add columns
        columns_to_add = ['medium_voltage', 'low_voltage', 'control_voltage']
        for column in columns_to_add:
            try:
                cursor_plants.execute(f'ALTER TABLE plants ADD COLUMN {column} TEXT')
                print(f'Columna "{column}" añadida a la tabla de plantas.')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f'La columna "{column}" ya existe en la tabla de plantas.')
                else:
                    raise e
        conn_plants.commit()
    except sqlite3.Error as e:
        print(f"Error with plants.db: {e}")
    finally:
        if conn_plants:
            conn_plants.close()

if __name__ == '__main__':
    migrate()