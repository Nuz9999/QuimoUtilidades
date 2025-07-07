####################################### NO MODIFICAR, OK YA! :D ###########################################
# importar_excel.py

import pandas as pd
import sqlite3
import os

def importar_excel_a_sqlite():
    ruta_excel = os.path.join("recursos", "inventario.xlsx")

    try:
        # Leer hoja llamada "existencias"
        df = pd.read_excel(ruta_excel, sheet_name="EXISTENCIAS")

        # Asegurarse de que las columnas coincidan
        columnas_esperadas = [
            "CODIGO", "MATERIAL/PRODUCTO", "UNIDAD DE MEDIDA",
            "AREA", "EXISTENCIA", "ESTATUS"
        ]
        if not all(col in df.columns for col in columnas_esperadas):
            raise ValueError("❌ Las columnas del archivo no coinciden con las esperadas.")

        # Renombrar columnas para que coincidan con la tabla
        df = df.rename(columns={
            "CODIGO": "codigo",
            "MATERIAL/PRODUCTO": "descripcion",
            "UNIDAD DE MEDIDA": "unidad_medida",
            "AREA": "area",
            "EXISTENCIA": "existencia",
            "ESTATUS": "estatus"
        })

        # Conexión a SQLite
        conn = sqlite3.connect("inventario.db")
        df.to_sql("productos", conn, if_exists="replace", index=False)
        conn.close()

        print("✅ Datos importados correctamente desde la hoja 'EXISTENCIAS'.")

    except Exception as e:
        print("❌ Error al importar el Excel:", e)

if __name__ == "__main__":
    importar_excel_a_sqlite()
