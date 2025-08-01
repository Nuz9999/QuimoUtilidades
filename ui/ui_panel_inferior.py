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
from contextlib import contextmanager


class PanelInferior(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        
        # Configuración inicial
        self.config = configparser.ConfigParser()
        try:
            self.config.read('config.ini')
            if not self.config.has_section('database'):
                raise configparser.NoSectionError('database')
        except Exception as e:
            QMessageBox.critical(self, "Error de configuración", 
                               f"No se pudo leer el archivo config.ini:\n{e}")
        
        # Inicializar componentes de la UI
        self.init_ui()
        
        # Verificar tablas necesarias
        self.tiene_compras = self.verificar_existencia_tabla('compras_materia_prima')
        self.tiene_recetas = self.verificar_existencia_tabla('recetas')
        
        if not self.tiene_recetas:
            QMessageBox.warning(self, "Advertencia", 
                              "La tabla 'recetas' no existe. La funcionalidad de costos estará limitada.")

    def init_ui(self):
        """Inicializa todos los componentes de la interfaz de usuario"""
        # Crear pestañas
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)
        
        # Pestaña de Producción
        self.setup_tab_produccion()
        
        # Pestaña de Costos
        self.setup_tab_costos()
        
        # Pestaña de Compras (si existe)
        if self.verificar_existencia_tabla('compras_materia_prima'):
            self.setup_tab_compras()

    @contextmanager
    def db_connection(self):
        """Context manager para manejar conexiones a la base de datos"""
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=self.config.get('database', 'dbname'),
                user=self.config.get('database', 'user'),
                password=self.config.get('database', 'password'),
                host=self.config.get('database', 'host'),
                port=self.config.get('database', 'port')
            )
            yield conn
        except Exception as e:
            QMessageBox.critical(self, "Error de conexión", 
                               f"No se pudo conectar a la base de datos:\n{e}")
            raise
        finally:
            if conn:
                conn.close()

    def verificar_existencia_tabla(self, nombre_tabla):
        """Verifica si una tabla existe en la base de datos"""
        try:
            with self.db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        );
                    """, (nombre_tabla,))
                    return cursor.fetchone()[0]
        except Exception:
            return False

    def setup_tab_produccion(self):
        """Configura la pestaña de producción"""
        self.tab_produccion = QWidget()
        self.tabs.addTab(self.tab_produccion, "Producción")
        layout = QVBoxLayout()
        self.tab_produccion.setLayout(layout)
        
        # Cabecera
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Producción Semanal</b>"))
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_a_excel)
        header_layout.addWidget(self.btn_exportar)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Tabla de producción
        self.tabla_produccion = QTableWidget()
        self.tabla_produccion.setColumnCount(12)
        self.tabla_produccion.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", 
             "Total", "Costo Total", "Precio Venta", "Ganancia"]
        )
        self.tabla_produccion.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_produccion)

        # Botones
        btn_layout = QHBoxLayout()
        btn_cargar = QPushButton("Cargar Producción")
        btn_cargar.clicked.connect(self.cargar_datos_desde_db)
        btn_layout.addWidget(btn_cargar)
        
        self.btn_calcular_costos = QPushButton("Calcular Costos y Ganancias")
        self.btn_calcular_costos.clicked.connect(self.calcular_costos)
        btn_layout.addWidget(self.btn_calcular_costos)
        layout.addLayout(btn_layout)

        self.label_total_produccion = QLabel("")
        layout.addWidget(self.label_total_produccion)

    def setup_tab_costos(self):
        """Configura la pestaña de costos"""
        self.tab_costos = QWidget()
        self.tabs.addTab(self.tab_costos, "Costos")
        layout = QVBoxLayout()
        self.tab_costos.setLayout(layout)
        
        layout.addWidget(QLabel("<b>Costos de Producción</b>"))
        
        self.tabla_costos = QTableWidget()
        self.tabla_costos.setColumnCount(9)
        self.tabla_costos.setHorizontalHeaderLabels(
            ["Materia Prima", "Costo Unitario", "L", "M", "M", "J", "V", "S", "D"]
        )
        self.tabla_costos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_costos)

        # Totales
        self.layout_totales_costos = QHBoxLayout()
        self.label_total_costos = QLabel("")
        self.label_total_ganancias = QLabel("")
        self.label_margen_ganancia = QLabel("")
        
        self.layout_totales_costos.addWidget(self.label_total_costos)
        self.layout_totales_costos.addWidget(self.label_total_ganancias)
        self.layout_totales_costos.addWidget(self.label_margen_ganancia)
        layout.addLayout(self.layout_totales_costos)

    def setup_tab_compras(self):
        """Configura la pestaña de compras si existe la tabla"""
        self.tab_compras = QWidget()
        self.tabs.addTab(self.tab_compras, "Compras MP")
        layout = QVBoxLayout()
        self.tab_compras.setLayout(layout)
        
        layout.addWidget(QLabel("<b>Compras de Materia Prima</b>"))
        
        self.tabla_compras = QTableWidget()
        self.tabla_compras.setColumnCount(6)
        self.tabla_compras.setHorizontalHeaderLabels(
            ["Materia Prima", "Proveedor", "Fecha", "Cantidad", "Costo Unitario", "Total"]
        )
        self.tabla_compras.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_compras)
        
        # Totales
        self.layout_totales_compras = QHBoxLayout()
        self.label_total_semanal = QLabel("Total semanal: $0.00")
        self.label_total_mensual = QLabel("Total mensual: $0.00")
        self.layout_totales_compras.addWidget(self.label_total_semanal)
        self.layout_totales_compras.addWidget(self.label_total_mensual)
        layout.addLayout(self.layout_totales_compras)
        
        btn_cargar_compras = QPushButton("Cargar Compras")
        btn_cargar_compras.clicked.connect(self.cargar_compras_desde_db)
        layout.addWidget(btn_cargar_compras)

    def cargar_datos_desde_db(self):
        """Carga los datos de producción desde la base de datos"""
        try:
            with self.db_connection() as conn:
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

            if df.empty:
                QMessageBox.information(self, "Sin datos", "No hay datos de producción registrados")
                return

            self.procesar_datos_produccion(df)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer la base de datos:\n{e}")

    def procesar_datos_produccion(self, df):
        """Procesa los datos de producción para mostrarlos en la tabla"""
        self.df_produccion = df.copy()
        
        # Crear columna combinada de producto y unidad
        df["producto_unidad"] = df["producto"] + " (" + df["unidad"] + ")"
        
        # Pivotar los datos por día
        tabla = df.pivot(index=["id_producto", "producto_unidad"], 
                        columns="dia", 
                        values="cantidad").fillna(0)

        # Asegurar todas las columnas de días
        dias_orden = ["L", "M", "M", "J", "V", "S", "D"]
        for d in dias_orden:
            if d not in tabla.columns:
                tabla[d] = 0

        # Ordenar columnas y calcular totales
        tabla = tabla[dias_orden]
        tabla["Total"] = tabla.sum(axis=1)
        
        # Inicializar columnas de costos y ganancias
        tabla["Costo Total"] = 0.0
        tabla["Precio Venta"] = 0.0
        tabla["Ganancia"] = 0.0

        self.mostrar_tabla_produccion(tabla)

    def mostrar_tabla_produccion(self, df):
        """Muestra los datos de producción en la tabla"""
        if df.empty:
            self.tabla_produccion.setRowCount(0)
            self.label_total_produccion.setText("Sin datos")
            return

        self.tabla_produccion.setRowCount(df.shape[0])
        
        total_produccion = total_costo = total_venta = total_ganancia = 0

        for i, (index, row) in enumerate(df.iterrows()):
            id_producto, producto_unidad = index
            
            # Producto (unidad)
            self.tabla_produccion.setItem(i, 0, QTableWidgetItem(producto_unidad))
            
            # Días de la semana y total
            dias_ordenados = ["L", "M", "M", "J", "V", "S", "D", "Total"]
            for j, dia in enumerate(dias_ordenados, start=1):
                val = row.get(dia, 0)
                item = QTableWidgetItem(str(round(val, 2)))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_produccion.setItem(i, j, item)
                
                if dia == "Total":
                    total_produccion += val
            
            # Costos y ganancias
            for j, col in enumerate(["Costo Total", "Precio Venta", "Ganancia"], start=9):
                val = row.get(col, 0)
                item = QTableWidgetItem(f"${val:,.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_produccion.setItem(i, j, item)
                
                if col == "Costo Total":
                    total_costo += val
                elif col == "Precio Venta":
                    total_venta += val
                elif col == "Ganancia":
                    total_ganancia += val

        # Actualizar resumen
        self.label_total_produccion.setText(
            f"<b>Total producción: {total_produccion} unidades | "
            f"Costo total: ${total_costo:,.2f} | "
            f"Venta total: ${total_venta:,.2f} | "
            f"Ganancia: ${total_ganancia:,.2f}</b>"
        )

    def calcular_costos(self):
        """Calcula los costos de producción basados en las recetas"""
        if self.df_produccion is None or self.df_produccion.empty:
            QMessageBox.warning(self, "Sin datos", "Primero cargue los datos de producción")
            return

        if not self.tiene_recetas:
            QMessageBox.warning(self, "Tabla faltante", 
                              "La tabla 'recetas' no existe en la base de datos")
            return
            
        try:
            # Crear DataFrame para costos detallados
            dias = ["L", "M", "M", "J", "V", "S", "D"]
            costos_detallados = pd.DataFrame(0, 
                                           index=self.materias_primas["id_mp"], 
                                           columns=dias)
            
            costos_detallados["Materia Prima"] = self.materias_primas.set_index("id_mp")["nombre_mp"]
            costos_detallados["Costo Unitario"] = self.materias_primas.set_index("id_mp")["costo_unitario_mp"]
            
            # Calcular costos para cada producto
            for _, prod_row in self.df_produccion.iterrows():
                id_producto = prod_row["id_producto"]
                recetas_producto = self.recetas_df[self.recetas_df["producto_id"] == id_producto]
                
                for _, receta in recetas_producto.iterrows():
                    id_mp = receta["materia_prima_id"]
                    cantidad_mp = receta["cantidad"]
                    precio_mp = receta["precio"]
                    
                    # Distribuir el costo por día
                    for dia in dias:
                        if dia in prod_row and not pd.isna(prod_row[dia]):
                            cantidad_dia = prod_row[dia]
                            costo_dia = cantidad_dia * cantidad_mp * precio_mp
                            costos_detallados.loc[id_mp, dia] += costo_dia
            
            # Calcular totales
            costos_detallados["Total"] = costos_detallados[dias].sum(axis=1)
            self.df_costos = costos_detallados
            
            # Mostrar resultados
            self.mostrar_tabla_costos()
            self.calcular_ganancias()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron calcular los costos:\n{e}")

    def calcular_ganancias(self):
        """Calcula las ganancias basadas en los costos"""
        if self.df_produccion is None:
            return
            
        df = self.df_produccion.copy()
        
        for i, (index, row) in enumerate(df.iterrows()):
            id_producto, _ = index
            recetas_producto = self.recetas_df[self.recetas_df["producto_id"] == id_producto]
            costo_total = 0
            
            # Calcular costo total del producto
            for _, receta in recetas_producto.iterrows():
                cantidad_mp = receta["cantidad"]
                precio_mp = receta["precio"]
                costo_total += row["Total"] * cantidad_mp * precio_mp
            
            # Aplicar margen de ganancia (30%)
            precio_venta = costo_total * 1.30
            ganancia = precio_venta - costo_total
            
            # Actualizar valores
            df.loc[index, "Costo Total"] = costo_total
            df.loc[index, "Precio Venta"] = precio_venta
            df.loc[index, "Ganancia"] = ganancia
        
        # Actualizar y mostrar
        self.df_produccion = df
        self.mostrar_tabla_produccion(df)

    def mostrar_tabla_costos(self):
        """Muestra los costos detallados en la tabla"""
        if self.df_costos is None or self.df_costos.empty:
            self.tabla_costos.setRowCount(0)
            return

        dias = ["L", "M", "M", "J", "V", "S", "D"]
        self.tabla_costos.setRowCount(len(self.df_costos))
        self.tabla_costos.setColumnCount(len(dias) + 2)
        
        total_costos = 0
        
        for i, (_, row) in enumerate(self.df_costos.iterrows()):
            # Materia Prima
            self.tabla_costos.setItem(i, 0, QTableWidgetItem(row["Materia Prima"]))
            
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
        
        # Calcular métricas financieras
        total_ventas = total_costos * 1.30
        total_ganancias = total_ventas - total_costos
        margen_ganancia = (total_ganancias / total_ventas * 100) if total_ventas > 0 else 0
        
        # Actualizar resumen
        self.label_total_costos.setText(f"<b>Costo total: ${total_costos:,.2f}</b>")
        self.label_total_ganancias.setText(f"<b>Ganancia total: ${total_ganancias:,.2f}</b>")
        self.label_margen_ganancia.setText(f"<b>Margen de ganancia: {margen_ganancia:.2f}%</b>")

    def cargar_compras_desde_db(self):
        """Carga los datos de compras de materia prima"""
        if not self.tiene_compras:
            QMessageBox.warning(self, "Tabla faltante", 
                               "La tabla 'compras_materia_prima' no existe")
            return
            
        try:
            hoy = datetime.now()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            
            inicio_mes = datetime(hoy.year, hoy.month, 1)
            fin_mes = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            
            with self.db_connection() as conn:
                # Compras semanales
                query = """
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
                WHERE c.fecha_compra BETWEEN %s AND %s
                ORDER BY c.fecha_compra DESC;
                """
                df_semanal = pd.read_sql_query(query, conn, 
                                              params=(inicio_semana.date(), fin_semana.date()))
                
                # Total mensual
                query_mensual = """
                SELECT SUM(c.cantidad * c.precio_unitario) AS total_mensual
                FROM compras_materia_prima c
                WHERE c.fecha_compra BETWEEN %s AND %s;
                """
                total_mensual = pd.read_sql_query(query_mensual, conn,
                                                 params=(inicio_mes.date(), fin_mes.date()))
                total_mensual = total_mensual.iloc[0, 0] or 0

            self.df_compras = df_semanal
            self.mostrar_tabla_compras(total_mensual)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las compras:\n{e}")

    def mostrar_tabla_compras(self, total_mensual):
        """Muestra los datos de compras en la tabla"""
        if self.df_compras is None or self.df_compras.empty:
            self.tabla_compras.setRowCount(0)
            self.label_total_semanal.setText("Total semanal: $0.00")
            self.label_total_mensual.setText(f"Total mensual: ${total_mensual:,.2f}")
            return

        self.tabla_compras.setRowCount(len(self.df_compras))
        
        total_semanal = 0
        
        for i, row in self.df_compras.iterrows():
            # Materia Prima
            self.tabla_compras.setItem(i, 0, QTableWidgetItem(row["materia_prima"]))
            
            # Proveedor
            self.tabla_compras.setItem(i, 1, QTableWidgetItem(row["proveedor"]))
            
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
        
        # Actualizar resumen
        self.label_total_semanal.setText(f"<b>Total semanal: ${total_semanal:,.2f}</b>")
        self.label_total_mensual.setText(f"<b>Total mensual: ${total_mensual:,.2f}</b>")

    def exportar_a_excel(self):
        """Exporta los datos a Excel (función pendiente de implementación)"""
        QMessageBox.information(self, "En desarrollo", 
                              "La funcionalidad de exportación a Excel está en desarrollo")