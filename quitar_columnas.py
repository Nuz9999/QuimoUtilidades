import sqlite3

def limpiar_bd():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    # 1. Crear tabla temporal sin duplicados y con descripcion no nula ni vacía
    cursor.execute('DROP TABLE IF EXISTS productos_temp')
    cursor.execute('''
        CREATE TABLE productos_temp AS
        SELECT * FROM productos p1
        WHERE ROWID = (
            SELECT MIN(ROWID) FROM productos p2 WHERE p2.codigo = p1.codigo
        )
        AND descripcion IS NOT NULL AND TRIM(descripcion) != ''
    ''')

    # 2. Borrar tabla original productos (para poder renombrar)
    cursor.execute('DROP TABLE productos')

    # 3. Crear tabla nueva sin columnas proveedor y stock_minimo
    cursor.execute('''
        CREATE TABLE productos (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT NOT NULL,
            unidad_medida TEXT,
            area TEXT,
            existencia REAL DEFAULT 0,
            estatus TEXT
        )
    ''')

    # 4. Insertar datos filtrados en la nueva tabla productos,
    # copiando solo las columnas necesarias desde productos_temp
    cursor.execute('''
        INSERT INTO productos (codigo, descripcion, unidad_medida, area, existencia, estatus)
        SELECT codigo, descripcion, unidad_medida, area, existencia, estatus FROM productos_temp
    ''')

    # 5. Borrar tabla temporal productos_temp
    cursor.execute('DROP TABLE productos_temp')

    conexion.commit()
    conexion.close()
    print("✅ Base de datos limpiada: duplicados eliminados y columnas proveedor, stock_minimo quitadas.")

if __name__ == "__main__":
    limpiar_bd()
