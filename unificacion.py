import pandas as pd

archivo_excel = 'tu_archivo_con_hojas.xlsx'  # Cambia por tu archivo real

# Leer todas las hojas
hojas = pd.read_excel(archivo_excel, sheet_name=None)

lista_dfs = []

for nombre_hoja, df in hojas.items():
    print(f"Procesando hoja: {nombre_hoja}")

    # Buscar las columnas necesarias (case insensitive)
    col_producto = next((col for col in df.columns if 'materia prima' in col.lower()), None)
    col_proveedor = next((col for col in df.columns if 'proveedor' in col.lower()), None)
    col_precio = next((col for col in df.columns if 'precio' in col.lower()), None)

    if not col_producto or not col_proveedor or not col_precio:
        print(f"  ⚠️ No encontró todas las columnas necesarias en hoja '{nombre_hoja}', se salta.")
        continue

    # Extraer solo las columnas deseadas
    df_temp = df[[col_producto, col_proveedor, col_precio]].copy()

    # Renombrar para unificar nombres
    df_temp.columns = ['producto', 'proveedor', 'precio']

    # Limpiar precio: quitar $, comas y espacios
    df_temp['precio'] = df_temp['precio'].astype(str).str.replace('[\$,]', '', regex=True).str.strip()

    # Convertir precio a float, asignar NaN si no puede
    df_temp['precio'] = pd.to_numeric(df_temp['precio'], errors='coerce')

    # Quitar filas con producto o precio faltante
    df_temp.dropna(subset=['producto', 'precio'], inplace=True)

    lista_dfs.append(df_temp)

# Unir todas las hojas
df_final = pd.concat(lista_dfs, ignore_index=True)

# Eliminar duplicados por producto, manteniendo la primera fila encontrada
df_final = df_final.drop_duplicates(subset='producto', keep='first')

# Guardar a Excel final
df_final.to_excel('inventario_unificado_con_proveedor.xlsx', index=False)

print(f"\n✅ Archivo creado: inventario_unificado_con_proveedor.xlsx con {len(df_final)} productos únicos.")
