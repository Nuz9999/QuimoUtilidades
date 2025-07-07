import sqlite3

def listar_columnas(cursor):
    cursor.execute("PRAGMA table_info(productos)")
    columnas = cursor.fetchall()
    print("Columnas actuales en productos:")
    for col in columnas:
        print(f"- {col[1]} (tipo: {col[2]})")

def limpiar_bd():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    listar_columnas(cursor)  # Mostrar columnas antes de limpiar

    # El resto de tu código para limpiar la base:
    cursor.execute('DROP TABLE IF EXISTS productos_temp')
    cursor.execute('''
        CREATE TABLE productos_temp AS
        SELECT * FROM productos p1
        WHERE ROWID = (
            SELECT MIN(ROWID) FROM productos p2 WHERE p2.codigo = p1.codigo
        )
        AND descripcion IS NOT NULL AND TRIM(descripcion) != ''
    ''')

    cursor.execute('DROP TABLE productos')

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

    cursor.execute('''
        INSERT INTO productos (codigo, descripcion, unidad_medida, area, existencia, estatus)
        SELECT codigo, descripcion, unidad_medida, area, existencia, estatus FROM productos_temp
    ''')

    cursor.execute('DROP TABLE productos_temp')

    conexion.commit()
    conexion.close()
    print("✅ Base de datos limpiada: duplicados eliminados y columnas proveedor, stock_minimo quitadas.")

if __name__ == "__main__":
    limpiar_bd()
