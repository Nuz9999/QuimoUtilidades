from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox
)
import sqlite3
import pandas as pd
import os

from ui.ui_panel_derecho import PanelDerecho


class InventarioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Inventario")
        self.setMinimumSize(1000, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        self.init_ui()
        self.cargar_desde_sqlite()

        self.panel_derecho = PanelDerecho(self.tabla, self.cargar_desde_sqlite)
        self.main_layout.addWidget(self.panel_derecho)

    def init_ui(self):
        btn_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto...")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        btn_layout.addWidget(self.search_input)

        self.left_layout.addLayout(btn_layout)

        self.tabla = QTableWidget()
        self.left_layout.addWidget(self.tabla)

    def cargar_desde_sqlite(self):
        db_path = "inventario.db"
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Error", f"No se encontró la base de datos:\n{db_path}")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos")
            datos = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]
            conn.close()

            self.df_original = pd.DataFrame(datos, columns=columnas)
            self.mostrar_tabla(self.df_original)
        except Exception as e:
            print("❌ Error al cargar desde SQLite:", e)
            QMessageBox.critical(self, "Error", f"No se pudo cargar desde la base de datos:\n{e}")

    def mostrar_tabla(self, df):
        self.tabla.setRowCount(df.shape[0])
        self.tabla.setColumnCount(df.shape[1])
        self.tabla.setHorizontalHeaderLabels(df.columns)

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[i, j]))
                self.tabla.setItem(i, j, item)

    def filtrar_tabla(self, texto):
        if hasattr(self, "df_original"):
            df_filtrado = self.df_original[
                self.df_original.apply(
                    lambda row: any(texto.lower() in str(val).lower() for val in row), axis=1
                )
            ]
            self.mostrar_tabla(df_filtrado)
    