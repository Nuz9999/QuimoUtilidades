from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import psycopg2
import pandas as pd
import os
import configparser


class PanelInferior(QWidget):
    def __init__(self):
        super().__init__()

        self.setLayout(QVBoxLayout())
        
        # Sección de producción
        layout_produccion = QHBoxLayout()
        layout_produccion.addWidget(QLabel("<b>Producción Semanal</b>"))
        self.btn_exportar = QPushButton("Exportar a Excel")
        layout_produccion.addWidget(self.btn_exportar)
        layout_produccion.addStretch()
        self.layout().addLayout(layout_produccion)

        # Tabla de producción
        self.tabla_produccion = QTableWidget()
        self.layout().addWidget(self.tabla_produccion)

        self.tabla_produccion.setColumnCount(9)
        self.tabla_produccion.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", "Total"]
        )
        self.tabla_produccion.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Botones
        btn_layout = QHBoxLayout()
        btn_cargar = QPushButton("Cargar Producción")
        btn_cargar.clicked.connect(self.cargar_datos_desde_db)
        btn_layout.addWidget(btn_cargar)
        
        self.btn_calcular_costos = QPushButton("Calcular Costos")
        self.btn_calcular_costos.clicked.connect(self.calcular_costos)
        btn_layout.addWidget(self.btn_calcular_costos)
        self.layout().addLayout(btn_layout)

        self.label_total_produccion = QLabel("")
        self.layout().addWidget(self.label_total_produccion)

        # Sección de costos
        self.layout().addWidget(QLabel("<b>Costos de Producción</b>"))
        
        # Tabla de costos
        self.tabla_costos = QTableWidget()
        self.layout().addWidget(self.tabla_costos)
        self.tabla_costos.setColumnCount(8)
        self.tabla_costos.setHorizontalHeaderLabels(
            ["L", "M", "M", "J", "V", "S", "D", "Total"]
        )
        self.tabla_costos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.label_total_costos = QLabel("")
        self.layout().addWidget(self.label_total_costos)

        # Variables para almacenar datos
        self.df_produccion = None
        self.df_costos = None

        # Configuración de la base de datos
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
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
                p.nombre_producto AS producto,
                p.unidad_medida_producto AS unidad,
                pr.dia,
                SUM(pr.cantidad) as cantidad
            FROM produccion pr
            JOIN productos p ON pr.producto_id = p.id_producto
            GROUP BY p.nombre_producto, p.unidad_medida_producto, pr.dia
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                QMessageBox.information(self, "Sin datos", "No hay datos de producción registrados")
                return

            # Guardar el DataFrame para usar en el cálculo de costos
            self.df_produccion = df.copy()

            # Procesar datos para mostrar
            df["producto_unidad"] = df["producto"] + " (" + df["unidad"] + ")"
            tabla = df.pivot(index="producto_unidad", columns="dia", values="cantidad").fillna(0)

            # Asegurar columnas en orden de semana
            dias_orden = ["L", "M", "M", "J", "V", "S", "D"]
            for d in dias_orden:
                if d not in tabla.columns:
                    tabla[d] = 0

            tabla = tabla[dias_orden]
            tabla["Total"] = tabla.sum(axis=1)

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
        self.tabla_produccion.setColumnCount(df.shape[1] + 1)
        self.tabla_produccion.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", "Total"]
        )

        total_mensual = 0

        for i, (producto_unidad, row) in enumerate(df.iterrows()):
            self.tabla_produccion.setItem(i, 0, QTableWidgetItem(producto_unidad))
            for j, val in enumerate(row):
                val = round(val, 2)
                if j == 7:  # Total por producto
                    total_mensual += val
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_produccion.setItem(i, j+1, item)

        self.label_total_produccion.setText(f"<b>Total producción acumulada: {total_mensual} unidades</b>")

    def calcular_costos(self):
        if self.df_produccion is None or self.df_produccion.empty:
            QMessageBox.warning(self, "Sin datos", "Primero cargue los datos de producción")
            return

        try:
            conn = self.get_db_connection()
            if not conn:
                return
                
            # Obtener todas las recetas
            recetas_query = """
            SELECT 
                p.nombre_producto AS producto_terminado,
                mp.nombre_mp AS materia_prima,
                r.cantidad_mp_por_unidad AS cantidad,
                COALESCE(mp.costo_unitario_mp, 0) AS precio
            FROM recetas r
            JOIN productos p ON r.producto_id = p.id_producto
            JOIN materiasprimas mp ON r.materia_prima_id = mp.id_mp
            """
            
            recetas_df = pd.read_sql_query(recetas_query, conn)
            
            if recetas_df.empty:
                QMessageBox.information(self, "Sin recetas", "No hay recetas definidas en la base de datos")
                conn.close()
                return
                
            # Calcular costos
            costos = {dia: 0.0 for dia in ["L", "M", "M", "J", "V", "S", "D"]}
            costos["Total"] = 0.0
            
            for _, row in self.df_produccion.iterrows():
                producto = row['producto']
                dia = row['dia']
                cantidad_producida = row['cantidad']
                
                # Filtrar recetas para este producto
                recetas_producto = recetas_df[recetas_df['producto_terminado'] == producto]
                
                for _, receta in recetas_producto.iterrows():
                    cantidad_mp = receta['cantidad']
                    precio_mp = receta['precio']
                    
                    # Calcular costo para esta materia prima
                    costo_dia = cantidad_producida * cantidad_mp * precio_mp
                    costos[dia] += costo_dia
                    costos["Total"] += costo_dia
            
            # Crear DataFrame para mostrar
            self.df_costos = pd.DataFrame([costos])
            self.mostrar_tabla_costos()
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron calcular los costos:\n{e}")

    def mostrar_tabla_costos(self):
        if self.df_costos is None or self.df_costos.empty:
            self.tabla_costos.setRowCount(0)
            self.tabla_costos.setColumnCount(0)
            self.label_total_costos.setText("Sin datos de costos")
            return

        # Configurar tabla
        self.tabla_costos.setRowCount(1)
        self.tabla_costos.setColumnCount(8)
        self.tabla_costos.setHorizontalHeaderLabels(
            ["L", "M", "M", "J", "V", "S", "D", "Total"]
        )
        
        # Llenar con datos
        dias = ["L", "M", "M", "J", "V", "S", "D", "Total"]
        total_costos = 0
        
        for j, dia in enumerate(dias):
            costo = self.df_costos[dia].iloc[0]
            item = QTableWidgetItem(f"${costo:,.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_costos.setItem(0, j, item)
            
            if dia == "Total":
                total_costos = costo
        
        self.label_total_costos.setText(f"<b>Costo total de producción: ${total_costos:,.2f}</b>")

    def exportar_a_excel(self):
        # Implementación pendiente
        pass