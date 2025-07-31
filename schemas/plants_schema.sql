-- schemas/plants_schema.sql

CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    cliente TEXT,
    sigla TEXT,
    pais TEXT,
    elevacion REAL,
    humedad REAL,
    medium_voltage TEXT,
    low_voltage TEXT,
    control_voltage TEXT
);