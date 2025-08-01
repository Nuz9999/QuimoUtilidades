from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox
)
import psycopg2
import pandas as pd
import configparser

from ui.ui_panel_derecho import PanelDerecho
from ui.ui_panel_inferior import PanelInferior

from PyQt6.QtCore import Qt


class InventarioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Inventario")
        self.setMinimumSize(1000, 600)

        # Configuración de la base de datos
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        self.init_ui()
        self.cargar_desde_postgres()

        self.panel_derecho = PanelDerecho(self.tabla, self.cargar_desde_postgres)
        self.main_layout.addWidget(self.panel_derecho)

    def init_ui(self):
        btn_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto...")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        btn_layout.addWidget(self.search_input)

        self.left_layout.addLayout(btn_layout)

        self.tabla = QTableWidget()
        self.tabla.itemSelectionChanged.connect(self.actualizar_panel_inferior)
        self.left_layout.addWidget(self.tabla)

        # Panel inferior
        self.panel_inferior = PanelInferior()
        self.left_layout.addWidget(self.panel_inferior)

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

    def filtrar_tabla(self, texto):
        if hasattr(self, "df_original"):
            if texto.strip() == "":
                self.mostrar_tabla(self.df_original)
                return

        df_filtrado = self.df_original[
            self.df_original.apply(
                lambda row: any(texto.lower() in str(val).lower() for val in row), axis=1
            )
        ]

        self.mostrar_tabla(df_filtrado)

    def cargar_desde_postgres(self):
        """Carga datos desde PostgreSQL en lugar de SQLite"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.id_producto,
                    p.nombre_producto,
                    p.unidad_medida_producto,
                    p.area_producto,
                    p.cantidad_producto as existencia,
                    p.estatus_producto,
                    COALESCE(pr.precio, 0) as precio
                FROM productos p
                LEFT JOIN precios_productos pr ON p.id_producto = pr.producto_id
                ORDER BY p.nombre_producto
            """)
            
            datos = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]
            conn.close()

            self.df_original = pd.DataFrame(datos, columns=columnas)
            self.mostrar_tabla(self.df_original)
            
        except Exception as e:
            print("❌ Error al cargar desde PostgreSQL:", e)
            QMessageBox.critical(self, "Error", f"No se pudo cargar desde la base de datos:\n{e}")

    def mostrar_tabla(self, df):
        if df is None or df.empty:
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(0)
            return

        self.tabla.setRowCount(df.shape[0])
        self.tabla.setColumnCount(df.shape[1])
        self.tabla.setHorizontalHeaderLabels(df.columns)

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[i, j]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla.setItem(i, j, item)

    def actualizar_panel_inferior(self):
        selected_items = self.tabla.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        try:
            precio = float(self.tabla.item(row, self.df_original.columns.get_loc("precio")).text())
        except Exception:
            precio = 0.0

        try:
            existencia = float(self.tabla.item(row, self.df_original.columns.get_loc("existencia")).text())
        except Exception:
            existencia = 0.0

        self.panel_inferior.calcular_y_actualizar(precio, existencia, "MXN")