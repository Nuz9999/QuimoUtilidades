from PyQt6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QCompleter, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
import sqlite3


class PanelDerecho(QTabWidget):
    def __init__(self, tabla_referencia, actualizar_tabla_callback):
        super().__init__()
        self.tabla_referencia = tabla_referencia
        self.actualizar_tabla_callback = actualizar_tabla_callback
        self.setFixedWidth(300)

        self.tab_entrada = self.crear_tab_entrada()
        self.tab_salida = self.crear_tab_salida()
        self.tab_gestion = self.crear_tab_gestion_productos()

        self.addTab(self.tab_entrada, "Entrada")
        self.addTab(self.tab_salida, "Salida")
        self.addTab(self.tab_gestion, "Productos")

        self.configurar_autocompletado()

    def configurar_autocompletado(self):
        try:
            conn = sqlite3.connect("inventario.db")
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, descripcion FROM productos")
            productos = cursor.fetchall()
            conn.close()

            codigos = [p[0] for p in productos]
            descripciones = [p[1] for p in productos]

            combined_list = list(set(codigos + descripciones))
            completer = QCompleter(combined_list)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

            self.codigo_entrada.setCompleter(completer)
            self.codigo_salida.setCompleter(completer)
            self.nuevo_codigo.setCompleter(completer)

        except Exception as e:
            print("❌ Error al configurar autocompletado:", e)

    def crear_linea_separadora(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setFrameShadow(QFrame.Shadow.Sunken)
        return linea

    def crear_tab_entrada(self):
        layout = QVBoxLayout()

        self.codigo_entrada = QLineEdit()
        self.codigo_entrada.setPlaceholderText("Código o Descripción")
        self.codigo_entrada.editingFinished.connect(lambda: self.autocompletar('entrada'))

        self.cantidad_entrada = QLineEdit()
        self.cantidad_entrada.setPlaceholderText("Cantidad")

        self.label_info_entrada = QLabel("...")

        btn_guardar = QPushButton("Guardar Entrada")
        btn_guardar.clicked.connect(self.registrar_entrada)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(lambda: self.limpiar_formulario("entrada"))

        layout.addWidget(QLabel("Registrar Entrada"))
        layout.addWidget(self.codigo_entrada)
        layout.addWidget(self.cantidad_entrada)
        layout.addWidget(self.label_info_entrada)
        layout.addWidget(btn_guardar)
        layout.addWidget(btn_cancelar)
        layout.addWidget(self.crear_linea_separadora())

        tab = QWidget()
        tab.setLayout(layout)
        return tab

    def crear_tab_salida(self):
        layout = QVBoxLayout()

        self.codigo_salida = QLineEdit()
        self.codigo_salida.setPlaceholderText("Código o Descripción")
        self.codigo_salida.editingFinished.connect(lambda: self.autocompletar('salida'))

        self.cantidad_salida = QLineEdit()
        self.cantidad_salida.setPlaceholderText("Cantidad")

        self.label_info_salida = QLabel("...")

        btn_guardar = QPushButton("Guardar Salida")
        btn_guardar.clicked.connect(self.registrar_salida)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(lambda: self.limpiar_formulario("salida"))

        layout.addWidget(QLabel("Registrar Salida"))
        layout.addWidget(self.codigo_salida)
        layout.addWidget(self.cantidad_salida)
        layout.addWidget(self.label_info_salida)
        layout.addWidget(btn_guardar)
        layout.addWidget(btn_cancelar)
        layout.addWidget(self.crear_linea_separadora())

        tab = QWidget()
        tab.setLayout(layout)
        return tab

    def crear_tab_gestion_productos(self):
        layout = QVBoxLayout()

        self.nuevo_codigo = QLineEdit()
        self.nuevo_codigo.setPlaceholderText("Código del producto")
        self.nuevo_codigo.editingFinished.connect(lambda: self.autocompletar("gestion"))

        self.nuevo_nombre = QLineEdit()
        self.nuevo_nombre.setPlaceholderText("Nombre o descripción")

        self.nueva_unidad = QLineEdit()
        self.nueva_unidad.setPlaceholderText("Unidad de medida")

        self.nuevo_area = QLineEdit()
        self.nuevo_area.setPlaceholderText("Área")

        self.nueva_existencia = QLineEdit()
        self.nueva_existencia.setPlaceholderText("Existencia")

        self.nuevo_estatus = QLineEdit()
        self.nuevo_estatus.setPlaceholderText("Estatus")
    
        self.nuevo_precio = QLineEdit()
        self.nuevo_precio.setPlaceholderText("Precio")

    # Aquí está el resumen bonito
        self.label_info_gestion = QLabel("...")
        self.label_info_gestion.setWordWrap(True)

        btn_agregar = QPushButton("Agregar/Actualizar Producto")
        btn_agregar.clicked.connect(self.guardar_producto)

        btn_baja = QPushButton("Dar de baja producto")
        btn_baja.clicked.connect(self.dar_de_baja_producto)

        layout.addWidget(QLabel("Gestión de Productos"))
        layout.addWidget(self.nuevo_codigo)
        layout.addWidget(self.nuevo_nombre)
        layout.addWidget(self.nueva_unidad)
        layout.addWidget(self.nuevo_area)
        layout.addWidget(self.nueva_existencia)
        layout.addWidget(self.nuevo_estatus)
        layout.addWidget(self.nuevo_precio)

        layout.addWidget(btn_agregar)
        layout.addWidget(btn_baja)

        layout.addWidget(self.label_info_gestion)  # añadimos aquí el resumen
        layout.addWidget(self.crear_linea_separadora())

        tab = QWidget()
        tab.setLayout(layout)
        self.configurar_autocompletado()
        return tab


    def autocompletar(self, destino):
        campo = {
            "entrada": self.codigo_entrada,
            "salida": self.codigo_salida,
            "gestion": self.nuevo_codigo
        }[destino]

        texto = campo.text().strip()
        if not texto:
            return

        try:
            conn = sqlite3.connect("inventario.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT codigo, descripcion, unidad_medida, area, existencia, estatus, precio "
                "FROM productos WHERE codigo=? OR descripcion=?", (texto, texto)
            )
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                codigo, descripcion, unidad, area, existencia, estatus, precio = resultado

                if destino == "entrada":
                    self.label_info_entrada.setText(f"{descripcion} | Stock: {existencia} {unidad}")
                elif destino == "salida":
                    self.label_info_salida.setText(f"{descripcion} | Stock: {existencia} {unidad}")
                elif destino == "gestion":
                    self.nuevo_codigo.setText(codigo)
                    self.nuevo_nombre.setText(descripcion)
                    self.nueva_unidad.setText(unidad)
                    self.nuevo_area.setText(area)
                    self.nuevo_estatus.setText(str(estatus))
                    self.nuevo_precio.setText(str(precio))
            else:
                if destino == "entrada":
                    self.label_info_entrada.setText("No encontrado.")
                elif destino == "salida":
                    self.label_info_salida.setText("No encontrado.")

        except Exception as e:
            print(f"❌ Error al autocompletar: {e}")

    def registrar_entrada(self):
        self.registrar_movimiento(self.codigo_entrada.text(), self.cantidad_entrada.text(), "entrada")

    def registrar_salida(self):
        self.registrar_movimiento(self.codigo_salida.text(), self.cantidad_salida.text(), "salida")

    def registrar_movimiento(self, texto, cantidad, tipo):
        if not texto or not cantidad:
            QMessageBox.warning(self, "Campos incompletos", "Por favor, completa todos los campos.")
            return

        try:
            cantidad = float(cantidad)
            if cantidad <= 0:
                raise ValueError
        except:
            QMessageBox.warning(self, "Cantidad inválida", "La cantidad debe ser positiva.")
            return

        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()
        cursor.execute("SELECT existencia FROM productos WHERE codigo=? OR descripcion=?", (texto, texto))
        resultado = cursor.fetchone()

        if not resultado:
            QMessageBox.critical(self, "Error", "Producto no encontrado.")
            conn.close()
            return

        stock_actual = resultado[0]
        nuevo_stock = stock_actual + cantidad if tipo == "entrada" else stock_actual - cantidad

        if nuevo_stock < 0:
            QMessageBox.critical(self, "Error", "No hay suficiente stock.")
            conn.close()
            return

        cursor.execute("UPDATE productos SET existencia=? WHERE codigo=? OR descripcion=?", (nuevo_stock, texto, texto))

        tabla = "entradas" if tipo == "entrada" else "salidas"
        cursor.execute(
            f"INSERT INTO {tabla} (fecha, codigo, cantidad, comentario) VALUES (datetime('now'), ?, ?, '')",
            (texto, cantidad)
        )

        conn.commit()
        conn.close()
        self.actualizar_tabla_callback()
        QMessageBox.information(self, "Éxito", f"{tipo.title()} registrada correctamente.")
        self.limpiar_formulario(tipo)

    def limpiar_formulario(self, tipo):
        if tipo == "entrada":
            self.codigo_entrada.clear()
            self.cantidad_entrada.clear()
            self.label_info_entrada.setText("...")
        elif tipo == "salida":
            self.codigo_salida.clear()
            self.cantidad_salida.clear()
            self.label_info_salida.setText("...")

    def guardar_producto(self):
        datos = {
            "codigo": self.nuevo_codigo.text().strip(),
            "descripcion": self.nuevo_nombre.text().strip(),
            "unidad": self.nueva_unidad.text().strip(),
            "area": self.nuevo_area.text().strip(),
            "estatus": self.nuevo_estatus.text().strip(),
            "precio": self.nuevo_precio.text().strip()
        }

        if not all(datos.values()):
            QMessageBox.warning(self, "Campos incompletos", "Por favor, llena todos los campos.")
            return

        try:
            conn = sqlite3.connect("inventario.db")
            cursor = conn.cursor()
            cursor.execute("SELECT codigo FROM productos WHERE codigo=?", (datos["codigo"],))
            existe = cursor.fetchone()

            if existe:
                cursor.execute(
                    """
                    UPDATE productos
                    SET descripcion=?, unidad_medida=?, area=?, estatus=?, precio=?
                    WHERE codigo=?
                    """, (datos["descripcion"], datos["unidad"], datos["area"],
                          datos["estatus"], datos["precio"], datos["codigo"])
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO productos (codigo, descripcion, unidad_medida, area, existencia, estatus, precio)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                    """, (datos["codigo"], datos["descripcion"], datos["unidad"],
                          datos["area"], datos["estatus"], datos["precio"])
                )

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Producto guardado correctamente.")
            self.limpiar_formulario("gestion")
            self.configurar_autocompletado()
            self.actualizar_tabla_callback()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el producto:\n{e}")

    def dar_de_baja_producto(self):
        codigo = self.nuevo_codigo.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Código vacío", "Escribe el código del producto.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar baja",
            f"¿Dar de baja el producto '{codigo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect("inventario.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM productos WHERE codigo=?", (codigo,))
                cambios = cursor.rowcount
                conn.commit()
                conn.close()

                if cambios:
                    QMessageBox.information(self, "Éxito", "Producto dado de baja.")
                    self.limpiar_formulario("gestion")
                    self.configurar_autocompletado()
                    self.actualizar_tabla_callback()
                else:
                    QMessageBox.information(self, "No encontrado", "No se encontró el producto.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo dar de baja:\n{e}")

    def limpiar_formulario_gestion(self):
        self.nuevo_codigo.clear()
        self.nuevo_nombre.clear()
        self.nueva_unidad.clear()
        self.nuevo_area.clear()
        self.nuevo_estatus.clear()
        self.nuevo_precio.clear()
