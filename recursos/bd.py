# bd.py

import sqlite3

def crear_bd():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    # Tabla: productos (existencias)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        codigo TEXT PRIMARY KEY,
        descripcion TEXT NOT NULL,
        proveedor TEXT,
        unidad TEXT,
        area TEXT,
        stock_minimo REAL DEFAULT 0,
        stock_actual REAL DEFAULT 0,
        estatus TEXT DEFAULT 'Activo'
    )
    ''')

    # Tabla: entradas (ingresos de materia prima)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entradas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        codigo TEXT NOT NULL,
        cantidad REAL NOT NULL,
        usuario TEXT,
        comentario TEXT,
        FOREIGN KEY(codigo) REFERENCES productos(codigo)
    )
    ''')

    # Tabla: salidas (consumo en producción)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        codigo TEXT NOT NULL,
        cantidad REAL NOT NULL,
        usuario TEXT,
        comentario TEXT,
        FOREIGN KEY(codigo) REFERENCES productos(codigo)
    )
    ''')

    # Tabla: usuarios (si decides usar roles en el sistema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('admin', 'operario')) NOT NULL
    )
    ''')

    conexion.commit()
    conexion.close()
    print("✅ Base de datos creada correctamente.")

if __name__ == "__main__":
    crear_bd()
