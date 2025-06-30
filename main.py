from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QRect
import sys
import sqlite3
import pandas as pd
import os

# ----------------- VENTANA PRINCIPAL -----------------
class InventarioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventario")
        self.setGeometry(0, 100, 600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto...")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.search_input)

        self.tabla = QTableWidget()
        layout.addWidget(self.tabla)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            conn = sqlite3.connect("inventario.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos")
            datos = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]
            conn.close()

            self.df_original = pd.DataFrame(datos, columns=columnas)
            self.mostrar_tabla(self.df_original)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la BD: {e}")

    def mostrar_tabla(self, df):
        self.tabla.setRowCount(df.shape[0])
        self.tabla.setColumnCount(df.shape[1])
        self.tabla.setHorizontalHeaderLabels(df.columns)
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.tabla.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

    def filtrar_tabla(self, texto):
        if hasattr(self, 'df_original'):
            df_filtrado = self.df_original[self.df_original.apply(
                lambda row: texto.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            self.mostrar_tabla(df_filtrado)

# ----------------- REGISTRAR ENTRADA -----------------
class VentanaEntrada(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Entrada")
        self.setGeometry(620, 100, 300, 200)

        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        layout.addWidget(QLabel("Aquí irá el formulario de entrada"))

# ----------------- REGISTRAR SALIDA -----------------
class VentanaSalida(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Salida")
        self.setGeometry(940, 100, 300, 200)

        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        layout.addWidget(QLabel("Aquí irá el formulario de salida"))

# ----------------- MAIN APP -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = InventarioApp()
    entrada_window = VentanaEntrada()
    salida_window = VentanaSalida()

    main_window.show()
    entrada_window.show()
    salida_window.show()

    sys.exit(app.exec())
