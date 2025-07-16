from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
import sqlite3
import pandas as pd
import os


class PanelInferior(QWidget):
    def __init__(self):
        super().__init__()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("<b>Producción Semanal</b>"))

        # Tabla
        self.tabla = QTableWidget()
        self.layout().addWidget(self.tabla)

        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", "Total"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Botón para calcular
        btn_cargar = QPushButton("Cargar y Calcular Totales")
        btn_cargar.clicked.connect(self.cargar_datos_desde_db)
        self.layout().addWidget(btn_cargar)

        self.label_mensual = QLabel("")
        self.layout().addWidget(self.label_mensual)

    def cargar_datos_desde_db(self):
        db_path = "inventario.db"
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Error", f"No se encontró la base de datos:\n{db_path}")
            return

        try:
            conn = sqlite3.connect(db_path)

            # Lee también la columna 'unidad'
            df = pd.read_sql_query(
                "SELECT producto, unidad, dia, SUM(cantidad) as cantidad "
                "FROM produccion GROUP BY producto, unidad, dia", conn
            )
            conn.close()

            if df.empty:
                QMessageBox.information(self, "Sin datos", "No hay datos en la tabla `produccion`.")
                return

            # Crea una nueva columna 'producto (unidad)'
            df["producto_unidad"] = df["producto"] + " (" + df["unidad"] + ")"

            # Pivot para mostrar como tabla semanal
            tabla = df.pivot(index="producto_unidad", columns="dia", values="cantidad").fillna(0)

            # Asegura las columnas en orden de semana
            dias_orden = ["L", "M", "M", "J", "V", "S", "D"]
            for d in dias_orden:
                if d not in tabla.columns:
                    tabla[d] = 0

            tabla = tabla[dias_orden]
            tabla["Total"] = tabla.sum(axis=1)

            self.mostrar_tabla(tabla)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer la base de datos:\n{e}")

    def mostrar_tabla(self, df):
        if df is None or df.empty:
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(0)
            self.label_mensual.setText("Sin datos")
            return

        self.tabla.setRowCount(df.shape[0])
        self.tabla.setColumnCount(df.shape[1] + 1)  # +1 para el producto (que ya incluye unidad)
        self.tabla.setHorizontalHeaderLabels(
            ["Producto (unidad)", "L", "M", "M", "J", "V", "S", "D", "Total"]
        )

        total_mensual = 0

        for i, (producto_unidad, row) in enumerate(df.iterrows()):
            self.tabla.setItem(i, 0, QTableWidgetItem(producto_unidad))
            for j, val in enumerate(row):
                val = round(val, 2)
                if j == 7:  # Total por producto
                    total_mensual += val
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(i, j+1, item)

        self.label_mensual.setText(f"<b>Total mensual acumulado: {total_mensual}</b>")
