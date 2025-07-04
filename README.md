# Aplicación de Cálculo Eléctrico

Esta es una aplicación web local desarrollada en Flask para el cálculo y dimensionamiento de cableado eléctrico según normativas.

## Características

-   Gestión de usuarios con 3 roles: Administrador, Ingeniero y Consultor.
-   Creación de proyectos para organizar los cálculos.
-   Importación de listas de equipos desde archivos Excel (.xlsx).
-   Cálculo de calibre de conductor basado en ampacidad y factores de corrección.
-   Cálculo de caída de tensión.
-   Generación de reportes en formato PDF y Excel.

## Instalación

1.  Clona este repositorio:
    `git clone https://github.com/CarlosTriana91/Electric.git`
2.  Navega a la carpeta del proyecto:
    `cd Electric`
3.  Crea un entorno virtual e instálalo:
    `python -m venv venv`
    `source venv/bin/activate`  # En Windows: `venv\Scripts\activate`
4.  Instala las dependencias:
    `pip install -r requirements.txt`
5.  Configura la base de datos (solo la primera vez):
    `python setup_database.py`
6.  Ejecuta la aplicación:
    `flask run`
7.  Abre tu navegador y ve a `http://127.0.0.1:5000`.