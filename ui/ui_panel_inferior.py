from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QHBoxLayout, QTabWidget
)
from PyQt6.QtCore import Qt
import psycopg2
import pandas as pd
import configparser
import numpy as np
from datetime import datetime, timedelta


class PanelInferior(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        
        # Crear pestañas para organizar mejor la información
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)
        
        # Pestaña de Producción
        self.tab_produccion = QWidget()
        self.tabs.addTab(self.tab_produccion, "Producción")
        self.tab_produccion.setLayout(QVBoxLayout())
        
        # Sección de producción
        layout_produccion = QHBoxLayout()
        layout_produccion.addWidget(QLabel("<b>Producción Semanal</b>"))
        self.btn_exportar = QPushButton("Exportar a Excel")
        layout_produccion.addWidget(self.btn_exportar)
        layout_produccion.addStretch()
        self.tab_produccion.layout().addLayout(layout_produccion)

        # Tabla de producción
        self.tabla_produccion = QTableWidget()
        self.tab_produccion.layout().addWidget(self.tabla_produccion)

        self.tabla_produccion.setColumnCount(12)  # Agregar columnas para costos y ganancias
        self.tabla_produccion.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", "Total", "Costo Total", "Precio Venta", "Ganancia"]
        )
        self.tabla_produccion.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Botones
        btn_layout = QHBoxLayout()
        btn_cargar = QPushButton("Cargar Producción")
        btn_cargar.clicked.connect(self.cargar_datos_desde_db)
        btn_layout.addWidget(btn_cargar)
        
        self.btn_calcular_costos = QPushButton("Calcular Costos y Ganancias")
        self.btn_calcular_costos.clicked.connect(self.calcular_costos)
        btn_layout.addWidget(self.btn_calcular_costos)
        self.tab_produccion.layout().addLayout(btn_layout)

        self.label_total_produccion = QLabel("")
        self.tab_produccion.layout().addWidget(self.label_total_produccion)

        # Pestaña de Costos
        self.tab_costos = QWidget()
        self.tabs.addTab(self.tab_costos, "Costos")
        self.tab_costos.setLayout(QVBoxLayout())
        
        # Sección de costos
        self.tab_costos.layout().addWidget(QLabel("<b>Costos de Producción</b>"))
        
        # Tabla de costos detallada
        self.tabla_costos = QTableWidget()
        self.tab_costos.layout().addWidget(self.tabla_costos)
        self.tabla_costos.setColumnCount(9)
        self.tabla_costos.setHorizontalHeaderLabels(
            ["Materia Prima", "Costo Unitario", "L", "M", "M", "J", "V", "S", "D"]
        )
        self.tabla_costos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Totales de costos
        self.layout_totales_costos = QHBoxLayout()
        self.label_total_costos = QLabel("")
        self.label_total_ganancias = QLabel("")
        self.label_margen_ganancia = QLabel("")
        
        self.layout_totales_costos.addWidget(self.label_total_costos)
        self.layout_totales_costos.addWidget(self.label_total_ganancias)
        self.layout_totales_costos.addWidget(self.label_margen_ganancia)
        
        self.tab_costos.layout().addLayout(self.layout_totales_costos)

        # Pestaña de Compras (se creará solo si existe la tabla)
        self.tab_compras = None
        self.tiene_compras = self.verificar_existencia_tabla('compras_materia_prima')
        self.tiene_recetas = self.verificar_existencia_tabla('recetas')
        
        if self.tiene_compras:
            self.crear_pestana_compras()

        # Variables para almacenar datos
        self.df_produccion = None
        self.df_costos = None
        self.df_compras = None
        self.recetas_df = None
        self.materias_primas = None

        # Configuración de la base de datos
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        if not self.tiene_recetas:
            QMessageBox.warning(self, "Advertencia", "La tabla 'recetas' no existe. La funcionalidad de costos estará limitada.")

    def crear_pestana_compras(self):
        """Crea la pestaña de compras si existe la tabla correspondiente"""
        self.tab_compras = QWidget()
        self.tabs.addTab(self.tab_compras, "Compras MP")
        self.tab_compras.setLayout(QVBoxLayout())
        
        # Sección de compras de materia prima
        self.tab_compras.layout().addWidget(QLabel("<b>Compras de Materia Prima</b>"))
        
        # Tabla de compras
        self.tabla_compras = QTableWidget()
        self.tab_compras.layout().addWidget(self.tabla_compras)
        self.tabla_compras.setColumnCount(6)
        self.tabla_compras.setHorizontalHeaderLabels(
            ["Materia Prima", "Proveedor", "Fecha", "Cantidad", "Costo Unitario", "Total"]
        )
        self.tabla_compras.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Totales de compras
        self.layout_totales_compras = QHBoxLayout()
        self.label_total_semanal = QLabel("Total semanal: $0.00")
        self.label_total_mensual = QLabel("Total mensual: $0.00")
        
        self.layout_totales_compras.addWidget(self.label_total_semanal)
        self.layout_totales_compras.addWidget(self.label_total_mensual)
        self.tab_compras.layout().addLayout(self.layout_totales_compras)
        
        btn_cargar_compras = QPushButton("Cargar Compras")
        btn_cargar_compras.clicked.connect(self.cargar_compras_desde_db)
        self.tab_compras.layout().addWidget(btn_cargar_compras)

    def verificar_existencia_tabla(self, nombre_tabla):
        """Verifica si una tabla existe en la base de datos"""
        try:
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{nombre_tabla}'
                    );
                """)
                existe = cursor.fetchone()[0]
                conn.close()
                return existe
            return False
        except Exception as e:
            print(f"Error al verificar tabla {nombre_tabla}: {e}")
            return False

    def get_db_connection(self):
        """Establece conexión con la base de datos PostgreSQL"""
        try:
            conn = psycopg2.connect(
                dbname=self.config.get('database', 'dbname'),
                user=self.config.get('database', 'user'),
                password=self.config.get('database', 'password'),
                host=self.config.get('database', 'host'),
                port=self.config.get('database', 'port')
            )
            return conn
        except Exception as e:
            QMessageBox.critical(self, "Error de conexión", f"No se pudo conectar a la base de datos:\n{e}")
            return None

    def cargar_datos_desde_db(self):
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            # Cargar datos de producción
            query = """
            SELECT 
                p.id_producto,
                p.nombre_producto AS producto,
                p.unidad_medida_producto AS unidad,
                pr.dia,
                SUM(pr.cantidad) as cantidad
            FROM produccion pr
            JOIN productos p ON pr.producto_id = p.id_producto
            GROUP BY p.id_producto, p.nombre_producto, p.unidad_medida_producto, pr.dia
            """
            
            df = pd.read_sql_query(query, conn)
            
            # Cargar recetas si existen
            if self.tiene_recetas:
                recetas_query = """
                SELECT 
                    r.producto_id,
                    r.materia_prima_id,
                    mp.nombre_mp AS materia_prima,
                    r.cantidad_mp_por_unidad AS cantidad,
                    COALESCE(mp.costo_unitario_mp, 0) AS precio
                FROM recetas r
                JOIN materiasprimas mp ON r.materia_prima_id = mp.id_mp
                """
                self.recetas_df = pd.read_sql_query(recetas_query, conn)
            else:
                self.recetas_df = pd.DataFrame()
            
            # Cargar materias primas
            mp_query = "SELECT id_mp, nombre_mp, costo_unitario_mp FROM materiasprimas"
            self.materias_primas = pd.read_sql_query(mp_query, conn)
            
            conn.close()

            if df.empty:
                QMessageBox.information(self, "Sin datos", "No hay datos de producción registrados")
                return

            # Guardar el DataFrame para usar en el cálculo de costos
            self.df_produccion = df.copy()

            # Procesar datos para mostrar
            df["producto_unidad"] = df["producto"] + " (" + df["unidad"] + ")"
            tabla = df.pivot(index=["id_producto", "producto_unidad"], columns="dia", values="cantidad").fillna(0)

            # Asegurar columnas en orden de semana
            dias_orden = ["L", "M", "M", "J", "V", "S", "D"]
            for d in dias_orden:
                if d not in tabla.columns:
                    tabla[d] = 0

            tabla = tabla[dias_orden]
            tabla["Total"] = tabla.sum(axis=1)

            # Inicializar columnas de costos y ganancias
            tabla["Costo Total"] = 0.0
            tabla["Precio Venta"] = 0.0
            tabla["Ganancia"] = 0.0

            self.mostrar_tabla_produccion(tabla)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer la base de datos:\n{e}")

    def mostrar_tabla_produccion(self, df):
        if df is None or df.empty:
            self.tabla_produccion.setRowCount(0)
            self.tabla_produccion.setColumnCount(0)
            self.label_total_produccion.setText("Sin datos")
            return

        self.tabla_produccion.setRowCount(df.shape[0])
        self.tabla_produccion.setColumnCount(12)
        self.tabla_produccion.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", "Total", "Costo Total", "Precio Venta", "Ganancia"]
        )

        total_produccion = 0
        total_costo = 0
        total_venta = 0
        total_ganancia = 0

        for i, (index, row) in enumerate(df.iterrows()):
            id_producto, producto_unidad = index
            
            # Columna 0: Producto
            self.tabla_produccion.setItem(i, 0, QTableWidgetItem(producto_unidad))
            
            # Columnas 1-8: Días y Total
            dias_ordenados = ["L", "M", "M", "J", "V", "S", "D", "Total"]
            for j, dia in enumerate(dias_ordenados, start=1):
                val = row[dia] if dia in row else 0
                item = QTableWidgetItem(str(round(val, 2)))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_produccion.setItem(i, j, item)
                
                if dia == "Total":
                    total_produccion += val
            
            # Columnas 9-11: Costo, Precio Venta, Ganancia
            for j, col in enumerate(["Costo Total", "Precio Venta", "Ganancia"], start=9):
                val = row[col] if col in row else 0
                item = QTableWidgetItem(f"${val:,.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_produccion.setItem(i, j, item)
                
                if col == "Costo Total":
                    total_costo += val
                elif col == "Precio Venta":
                    total_venta += val
                elif col == "Ganancia":
                    total_ganancia += val

        self.label_total_produccion.setText(
            f"<b>Total producción: {total_produccion} unidades | "
            f"Costo total: ${total_costo:,.2f} | "
            f"Venta total: ${total_venta:,.2f} | "
            f"Ganancia: ${total_ganancia:,.2f}</b>"
        )

    def calcular_costos(self):
        if self.df_produccion is None or self.df_produccion.empty:
            QMessageBox.warning(self, "Sin datos", "Primero cargue los datos de producción")
            return

        if not self.tiene_recetas:
            QMessageBox.warning(self, "Tabla faltante", "La tabla 'recetas' no existe en la base de datos")
            return
            
        try:
            # Crear DataFrame para costos detallados
            dias = ["L", "M", "M", "J", "V", "S", "D"]
            costos_detallados = pd.DataFrame(0, index=self.materias_primas["id_mp"], columns=dias)
            costos_detallados["Materia Prima"] = self.materias_primas.set_index("id_mp")["nombre_mp"]
            costos_detallados["Costo Unitario"] = self.materias_primas.set_index("id_mp")["costo_unitario_mp"]
            
            # Calcular costos para cada producto
            for _, prod_row in self.df_produccion.iterrows():
                id_producto = prod_row["id_producto"]
                
                # Filtrar recetas para este producto
                recetas_producto = self.recetas_df[self.recetas_df["producto_id"] == id_producto]
                
                for _, receta in recetas_producto.iterrows():
                    id_mp = receta["id_mp"]
                    cantidad_mp = receta["cantidad"]
                    precio_mp = receta["precio"]
                    
                    # Distribuir el costo por día
                    for dia in dias:
                        if dia in prod_row and not pd.isna(prod_row[dia]):
                            cantidad_dia = prod_row[dia]
                            costo_dia = cantidad_dia * cantidad_mp * precio_mp
                            if id_mp in costos_detallados.index:
                                costos_detallados.loc[id_mp, dia] += costo_dia
            
            # Calcular totales para la tabla de costos
            costos_detallados["Total"] = costos_detallados[dias].sum(axis=1)
            
            # Guardar para mostrar
            self.df_costos = costos_detallados
            self.mostrar_tabla_costos()
            
            # Calcular ganancias para la tabla de producción
            self.calcular_ganancias()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron calcular los costos:\n{e}")

    def calcular_ganancias(self):
        """Calcula ganancias del 30% para productos vendidos"""
        if self.df_produccion is None:
            return
            
        # Crear una copia para modificar
        df = self.df_produccion.copy()
        
        for i, (index, row) in enumerate(df.iterrows()):
            id_producto, _ = index
            
            # Obtener receta para este producto
            recetas_producto = self.recetas_df[self.recetas_df["producto_id"] == id_producto]
            costo_total = 0
            
            # Calcular costo total del producto
            for _, receta in recetas_producto.iterrows():
                cantidad_mp = receta["cantidad"]
                precio_mp = receta["precio"]
                # Usamos la producción total del producto
                costo_total += row["Total"] * cantidad_mp * precio_mp
            
            # Aplicar 30% de ganancia
            precio_venta = costo_total * 1.30
            ganancia = precio_venta - costo_total
            
            # Actualizar valores en el DataFrame
            df.loc[index, "Costo Total"] = costo_total
            df.loc[index, "Precio Venta"] = precio_venta
            df.loc[index, "Ganancia"] = ganancia
        
        # Actualizar y mostrar
        self.df_produccion = df
        self.mostrar_tabla_produccion(df)

    def mostrar_tabla_costos(self):
        if self.df_costos is None or self.df_costos.empty:
            self.tabla_costos.setRowCount(0)
            self.tabla_costos.setColumnCount(0)
            return

        # Configurar tabla
        dias = ["L", "M", "M", "J", "V", "S", "D"]
        self.tabla_costos.setRowCount(len(self.df_costos))
        self.tabla_costos.setColumnCount(len(dias) + 2)  # +2 para Materia Prima y Costo Unitario
        self.tabla_costos.setHorizontalHeaderLabels(
            ["Materia Prima", "Costo Unitario"] + dias
        )
        
        total_costos = 0
        
        for i, (_, row) in enumerate(self.df_costos.iterrows()):
            # Materia Prima
            item_mp = QTableWidgetItem(row["Materia Prima"])
            self.tabla_costos.setItem(i, 0, item_mp)
            
            # Costo Unitario
            item_cu = QTableWidgetItem(f"${row['Costo Unitario']:,.2f}")
            item_cu.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_costos.setItem(i, 1, item_cu)
            
            # Costos por día
            for j, dia in enumerate(dias, start=2):
                costo = row[dia]
                item = QTableWidgetItem(f"${costo:,.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_costos.setItem(i, j, item)
                
                total_costos += costo
        
        # Calcular ganancias
        total_ventas = total_costos * 1.30
        total_ganancias = total_ventas - total_costos
        margen_ganancia = (total_ganancias / total_ventas * 100) if total_ventas > 0 else 0
        
        # Actualizar labels
        self.label_total_costos.setText(f"<b>Costo total: ${total_costos:,.2f}</b>")
        self.label_total_ganancias.setText(f"<b>Ganancia total: ${total_ganancias:,.2f}</b>")
        self.label_margen_ganancia.setText(f"<b>Margen de ganancia: {margen_ganancia:.2f}%</b>")

    def cargar_compras_desde_db(self):
        if not self.tiene_compras:
            QMessageBox.warning(self, "Tabla faltante", "La tabla 'compras_materia_prima' no existe")
            return
            
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            # Calcular fechas para esta semana y este mes
            hoy = datetime.now()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            
            inicio_mes = datetime(hoy.year, hoy.month, 1)
            fin_mes = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            
            # Consulta para obtener compras
            query = f"""
            SELECT 
                mp.nombre_mp AS materia_prima,
                pv.nombre_proveedor AS proveedor,
                c.fecha_compra AS fecha,
                c.cantidad,
                c.precio_unitario,
                (c.cantidad * c.precio_unitario) AS total
            FROM compras_materia_prima c
            JOIN materiasprimas mp ON c.id_mp = mp.id_mp
            JOIN proveedor pv ON c.id_proveedor = pv.id_proveedor
            WHERE c.fecha_compra BETWEEN '{inicio_semana.date()}' AND '{fin_semana.date()}'
            ORDER BY c.fecha_compra DESC;
            """
            
            df_semanal = pd.read_sql_query(query, conn)
            
            # Consulta para compras mensuales
            query_mensual = f"""
            SELECT 
                SUM(c.cantidad * c.precio_unitario) AS total_mensual
            FROM compras_materia_prima c
            WHERE c.fecha_compra BETWEEN '{inicio_mes.date()}' AND '{fin_mes.date()}';
            """
            
            total_mensual = pd.read_sql_query(query_mensual, conn).iloc[0, 0] or 0
            
            conn.close()

            self.df_compras = df_semanal
            self.mostrar_tabla_compras(total_mensual)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las compras:\n{e}")

    def mostrar_tabla_compras(self, total_mensual):
        if self.df_compras is None or self.df_compras.empty:
            self.tabla_compras.setRowCount(0)
            self.tabla_compras.setColumnCount(0)
            self.label_total_semanal.setText("Total semanal: $0.00")
            self.label_total_mensual.setText(f"Total mensual: ${total_mensual:,.2f}")
            return

        # Configurar tabla
        self.tabla_compras.setRowCount(len(self.df_compras))
        self.tabla_compras.setColumnCount(6)
        self.tabla_compras.setHorizontalHeaderLabels(
            ["Materia Prima", "Proveedor", "Fecha", "Cantidad", "Costo Unitario", "Total"]
        )
        
        total_semanal = 0
        
        for i, row in self.df_compras.iterrows():
            # Materia Prima
            item_mp = QTableWidgetItem(row["materia_prima"])
            self.tabla_compras.setItem(i, 0, item_mp)
            
            # Proveedor
            item_prov = QTableWidgetItem(row["proveedor"])
            self.tabla_compras.setItem(i, 1, item_prov)
            
            # Fecha
            fecha = row["fecha"].strftime("%Y-%m-%d") if not pd.isna(row["fecha"]) else ""
            item_fecha = QTableWidgetItem(fecha)
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_compras.setItem(i, 2, item_fecha)
            
            # Cantidad
            item_cant = QTableWidgetItem(str(row["cantidad"]))
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_compras.setItem(i, 3, item_cant)
            
            # Costo Unitario
            item_cu = QTableWidgetItem(f"${row['precio_unitario']:,.2f}")
            item_cu.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_compras.setItem(i, 4, item_cu)
            
            # Total
            total = row["total"]
            item_total = QTableWidgetItem(f"${total:,.2f}")
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_compras.setItem(i, 5, item_total)
            
            total_semanal += total
        
        # Actualizar labels
        self.label_total_semanal.setText(f"<b>Total semanal: ${total_semanal:,.2f}</b>")
        self.label_total_mensual.setText(f"<b>Total mensual: ${total_mensual:,.2f}</b>")

    def exportar_a_excel(self):
        # Implementación de exportación a Excel
        QMessageBox.information(self, "En desarrollo", "La funcionalidad de exportación a Excel está en desarrollo")