import sqlite3

conexion = sqlite3.connect("inventario.db")
cursor = conexion.cursor()

try:
    cursor.execute("ALTER TABLE productos ADD COLUMN precio REAL DEFAULT 0")
    conexion.commit()
    print("✅ Columna 'precio' agregada correctamente.")
except sqlite3.OperationalError as e:
    print("⚠️ Ya existe la columna o error:", e)

conexion.close()
