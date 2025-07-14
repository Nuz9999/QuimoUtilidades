# Borrar todas las columnas de la db
import sqlite3

def eliminar_columnas(nombre_tabla, columnas_a_eliminar):
    try:
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()

        # Obtener todas las columnas actuales
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas_info = cursor.fetchall()
        columnas_actuales = [col[1] for col in columnas_info]

        # Filtrar columnas a mantener
        columnas_nuevas = [col for col in columnas_actuales if col not in columnas_a_eliminar]

        if not columnas_nuevas:
            print("❌ No puedes eliminar todas las columnas.")
            return

        columnas_nuevas_str = ", ".join(columnas_nuevas)

        # Crear nueva tabla con las columnas a mantener
        columnas_definicion = []
        for col in columnas_info:
            if col[1] in columnas_nuevas:
                columnas_definicion.append(f"{col[1]} {col[2]}")
        columnas_definicion_str = ", ".join(columnas_definicion)

        nombre_temporal = f"{nombre_tabla}_tmp"

        cursor.execute(f"CREATE TABLE {nombre_temporal} ({columnas_definicion_str})")
        cursor.execute(f"INSERT INTO {nombre_temporal} SELECT {columnas_nuevas_str} FROM {nombre_tabla}")
        cursor.execute(f"DROP TABLE {nombre_tabla}")
        cursor.execute(f"ALTER TABLE {nombre_temporal} RENAME TO {nombre_tabla}")

        conn.commit()
        conn.close()
        print(f"✅ Columnas {columnas_a_eliminar} eliminadas correctamente de la tabla '{nombre_tabla}'.")

    except Exception as e:
        print(f"❌ Error al eliminar columnas: {e}")
        
    import sqlite3

# Borrar columna especifica de la DB.
def eliminar_columna(nombre_tabla, columnas_a_eliminar):
    try:
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()

        # Obtener todas las columnas actuales
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas_info = cursor.fetchall()
        columnas_actuales = [col[1] for col in columnas_info]

        # Filtrar columnas a mantener
        columnas_nuevas = [col for col in columnas_actuales if col not in columnas_a_eliminar]

        if not columnas_nuevas:
            print("❌ No puedes eliminar todas las columnas.")
            return

        columnas_nuevas_str = ", ".join(columnas_nuevas)

        # Crear nueva tabla con las columnas a mantener
        columnas_definicion = []
        for col in columnas_info:
            if col[1] in columnas_nuevas:
                columnas_definicion.append(f"{col[1]} {col[2]}")
        columnas_definicion_str = ", ".join(columnas_definicion)

        nombre_temporal = f"{nombre_tabla}_tmp"

        cursor.execute(f"CREATE TABLE {nombre_temporal} ({columnas_definicion_str})")
        cursor.execute(f"INSERT INTO {nombre_temporal} SELECT {columnas_nuevas_str} FROM {nombre_tabla}")
        cursor.execute(f"DROP TABLE {nombre_tabla}")
        cursor.execute(f"ALTER TABLE {nombre_temporal} RENAME TO {nombre_tabla}")

        conn.commit()
        conn.close()
        print(f"✅ Columnas {columnas_a_eliminar} eliminadas correctamente de la tabla '{nombre_tabla}'.")

    except Exception as e:
        print(f"❌ Error al eliminar columnas: {e}")
        
# Limpiar datos de columnas especificas
import sqlite3

def limpiar_columnas(nombre_tabla, columnas_a_limpiar, usar_null=True):
    try:
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()

        # Verificar que las columnas existan
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas_info = [col[1] for col in cursor.fetchall()]
        columnas_validas = [col for col in columnas_a_limpiar if col in columnas_info]

        if not columnas_validas:
            print("❌ Ninguna de las columnas especificadas existe en la tabla.")
            return

        # Construir consulta de actualización
        valor = "NULL" if usar_null else "''"
        set_clause = ", ".join([f"{col} = {valor}" for col in columnas_validas])
        query = f"UPDATE {nombre_tabla} SET {set_clause}"
        cursor.execute(query)

        conn.commit()
        conn.close()
        print(f"✅ Columnas {columnas_validas} limpiadas correctamente en la tabla '{nombre_tabla}'.")
    except Exception as e:
        print(f"❌ Error al limpiar columnas: {e}")
        
# Predeterminar valores Nulos.
import sqlite3

def rellenar_nulos(nombre_tabla, valores_por_columna):
    try:
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()

        # Obtener columnas actuales de la tabla
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas_info = [col[1] for col in cursor.fetchall()]

        # Filtrar columnas válidas
        columnas_validas = {
            col: valor for col, valor in valores_por_columna.items() if col in columnas_info
        }

        if not columnas_validas:
            print("❌ Ninguna de las columnas especificadas existe en la tabla.")
            return

        for columna, valor in columnas_validas.items():
            cursor.execute(f"UPDATE {nombre_tabla} SET {columna} = ? WHERE {columna} IS NULL", (valor,))
            print(f"✅ Valores NULL en columna '{columna}' fueron reemplazados con: {valor}")

        conn.commit()
        conn.close()
        print("✅ Todos los valores NULL han sido actualizados exitosamente.")

    except Exception as e:
        print(f"❌ Error al actualizar valores NULL: {e}")


# Ejemplo de uso:
if __name__ == "__main__":
    tabla = "productos"
    
    # Borrar
    #columnas_a_eliminar = ["REAL"]  # <-- modifica aquí las columnas a eliminar
    #eliminar_columna(tabla, columnas_a_eliminar)
    
    # Limpiar
    #columnas = ["existencia", "estatus", "precio"]  # <-- modifica aquí las columnas a limpiar
    #limpiar_columnas(tabla, columnas, usar_null=True)  # usar_null=True para NULL, False para texto vacío
    
    # Predeterminar valores Nulos
    # Define qué valor usar para reemplazar NULL en cada columna
    valores_predeterminados = {
        "existencia": 0,
        "estatus": 0,
        "precio": 0.0
    }

    rellenar_nulos(tabla, valores_predeterminados)
