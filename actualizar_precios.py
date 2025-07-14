import sqlite3
import csv

DB_PATH = "inventario.db"
CSV_PATH = "precios_comparados_revisado.csv"  # <- nombre corregido

def actualizar_precios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    actualizados = []
    no_encontrados = []

    # Verificar que la tabla productos y columnas existen (opcional de depuración)
    try:
        cursor.execute("PRAGMA table_info(productos)")
        columnas = [col[1] for col in cursor.fetchall()]
        if not all(col in columnas for col in ["codigo", "descripcion", "precio"]):
            print("❌ La tabla 'productos' no contiene las columnas requeridas.")
            return
    except sqlite3.OperationalError as e:
        print(f"❌ Error accediendo a la tabla: {e}")
        return

    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # saltar cabecera
        for linea in reader:
            codigo, precio = linea[0].strip(), linea[1].strip()

            try:
                precio = float(precio)
            except ValueError:
                print(f"⚠️ Precio inválido para '{codigo}': '{precio}'")
                continue

            cursor.execute(
                "UPDATE productos SET precio=? WHERE codigo=? OR descripcion=?",
                (precio, codigo, codigo)
            )

            if cursor.rowcount > 0:
                print(f"✔️ Producto actualizado: {codigo}")
                actualizados.append(codigo)
            else:
                print(f"❌ No encontrado: {codigo}")
                no_encontrados.append(codigo)

    conn.commit()
    conn.close()

    print("\n✅ Actualización terminada.")
    if actualizados:
        print(f"\n📋 Productos actualizados ({len(actualizados)}):")
        for c in actualizados:
            print(f" - {c}")
    if no_encontrados:
        print(f"\n🚫 No encontrados ({len(no_encontrados)}):")
        for c in no_encontrados:
            print(f" - {c}")

if __name__ == "__main__":
    actualizar_precios()
