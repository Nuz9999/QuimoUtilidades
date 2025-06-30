import sqlite3

conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()

# Mostrar nombres de las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("📋 Tablas en la base de datos:", cursor.fetchall())

# Mostrar los primeros registros de la tabla productos
cursor.execute("SELECT * FROM productos LIMIT 163;")
registros = cursor.fetchall()
print("🧾 Primeros productos cargados:")
for r in registros:
    print(r)

conn.close()
