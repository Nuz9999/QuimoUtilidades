import sqlite3

def listar_columnas():
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()

    cursor.execute("PRAGMA table_info(productos)")
    columnas = cursor.fetchall()

    print("Columnas en la tabla 'productos':")
    for col in columnas:
        # col[1] es el nombre de la columna
        print(f"- {col[1]} (tipo: {col[2]})")

    conexion.close()

if __name__ == "__main__":
    listar_columnas()
