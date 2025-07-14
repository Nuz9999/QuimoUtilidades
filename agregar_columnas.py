import sqlite3

def agregar_columna(nombre_tabla, nombre_columna, tipo_dato):
    try:
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()

        # Verificar si la columna ya existe
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        if nombre_columna in columnas_existentes:
            print(f"⚠️ La columna '{nombre_columna}' ya existe en la tabla '{nombre_tabla}'.")
            return

        # Agregar nueva columna
        cursor.execute(f"ALTER TABLE {nombre_tabla} ADD COLUMN {nombre_columna} {tipo_dato}")
        conn.commit()
        conn.close()
        print(f"✅ Columna '{nombre_columna}' ({tipo_dato}) añadida exitosamente a la tabla '{nombre_tabla}'.")

    except Exception as e:
        print(f"❌ Error al agregar columna: {e}")

# 🧪 Ejecución interactiva
if __name__ == "__main__":
    print("=== Agregar nueva columna a una tabla en inventario.db ===")
    tabla = input("📦 Nombre de la tabla: ").strip()
    columna = input("🆕 Nombre de la nueva columna: ").strip()
    tipo = input("🔤 Tipo de dato (INTEGER, TEXT, REAL, etc.): ").strip().upper()

    agregar_columna(tabla, columna, tipo)
