import sqlite3

def eliminar_duplicados():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    # Crear tabla temporal sin duplicados, seleccionando la fila con menor ROWID para cada código
    cursor.execute('''
        CREATE TABLE productos_sin_duplicados AS
        SELECT * FROM productos p1
        WHERE ROWID = (
            SELECT MIN(ROWID) FROM productos p2 WHERE p2.codigo = p1.codigo
        )
    ''')

    # Borrar tabla original
    cursor.execute('DROP TABLE productos')

    # Renombrar tabla nueva
    cursor.execute('ALTER TABLE productos_sin_duplicados RENAME TO productos')

    conexion.commit()
    conexion.close()
    print("✅ Duplicados eliminados, solo quedó una fila por código.")

if __name__ == "__main__":
    eliminar_duplicados()
