from PyQt6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QCompleter, QFrame, QMessageBox,
    QDialog, QSpinBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import psycopg2
import configparser


class VentanaActualizacionMultiple(QDialog):
    def __init__(self, parent=None, productos=None):
        super().__init__(parent)
        self.setWindowTitle("Actualizar precios de varios productos")
        self.setMinimumWidth(400)

        self.productos = productos or []
        self.parent = parent  # Guardar referencia al padre para acceder a la conexión

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("¿Cuántos productos actualizarás?"))

        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(50)
        self.layout.addWidget(self.spin_cantidad)

        btn_generar = QPushButton("Generar campos")
        btn_generar.clicked.connect(self.generar_campos)
        self.layout.addWidget(btn_generar)

        self.campos_layout = QVBoxLayout()
        self.layout.addLayout(self.campos_layout)

        self.btn_guardar = QPushButton("Guardar todos los cambios")
        self.btn_guardar.clicked.connect(self.guardar_cambios)
        self.btn_guardar.setEnabled(False)
        self.layout.addWidget(self.btn_guardar)

        self.campos = []  # para guardar las referencias a los campos

    def generar_campos(self):
        # limpiar anteriores
        for i in reversed(range(self.campos_layout.count())):
            item = self.campos_layout.itemAt(i).widget()
            if item:
                item.deleteLater()
        self.campos.clear()

        cantidad = self.spin_cantidad.value()

        for i in range(cantidad):
            h = QHBoxLayout()
            le_codigo_desc = QLineEdit()
            le_codigo_desc.setPlaceholderText(f"ID o Nombre #{i+1}")

            # autocompletado aquí
            completer = QCompleter(self.productos)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            le_codigo_desc.setCompleter(completer)

            le_precio = QLineEdit()
            le_precio.setPlaceholderText(f"Nuevo precio #{i+1}")

            h.addWidget(le_codigo_desc)
            h.addWidget(le_precio)

            self.campos_layout.addLayout(h)
            self.campos.append((le_codigo_desc, le_precio))

        self.btn_guardar.setEnabled(True)

    def guardar_cambios(self):
        errores = []
        conn = None
        try:
            conn = self.parent.get_db_connection()
            cursor = conn.cursor()

            for idx, (le_cd, le_precio) in enumerate(self.campos):
                cd = le_cd.text().strip()
                precio_texto = le_precio.text().strip()

                if not cd or not precio_texto:
                    errores.append(f"Producto #{idx+1}: campos vacíos")
                    continue

                try:
                    precio = float(precio_texto)
                except ValueError:
                    errores.append(f"Producto #{idx+1}: precio inválido")
                    continue

                # Intentar convertir a entero si parece un ID
                try:
                    producto_id = int(cd)
                    cursor.execute(
                        "UPDATE productos SET precio_venta=%s WHERE id_producto=%s",
                        (precio, producto_id)
                    )
                except ValueError:
                    # Si no es un número, buscar por nombre
                    cursor.execute(
                        "UPDATE productos SET precio_venta=%s WHERE nombre_producto=%s",
                        (precio, cd)
                    )

                if cursor.rowcount == 0:
                    errores.append(f"Producto #{idx+1}: no encontrado")

            conn.commit()

            if errores:
                QMessageBox.warning(self, "Errores", "\n".join(errores))
            else:
                QMessageBox.information(self, "Éxito", "Precios actualizados correctamente.")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de base de datos:\n{e}")
        finally:
            if conn:
                conn.close()


class PanelDerecho(QTabWidget):
    def __init__(self, tabla_referencia, actualizar_tabla_callback):
        super().__init__()
        self.tabla_referencia = tabla_referencia
        self.actualizar_tabla_callback = actualizar_tabla_callback
        self.setFixedWidth(300)

        # Configuración de la base de datos
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.tab_entrada = self.crear_tab_entrada()
        self.tab_salida = self.crear_tab_salida()
        self.tab_gestion = self.crear_tab_gestion_productos()

        self.addTab(self.tab_entrada, "Entrada")
        self.addTab(self.tab_salida, "Salida")
        self.addTab(self.tab_gestion, "Productos")

        self.configurar_autocompletado()

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

    def configurar_autocompletado(self):
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            cursor = conn.cursor()
            cursor.execute("SELECT id_producto, nombre_producto FROM productos")
            productos = cursor.fetchall()
            conn.close()

            # Crear lista combinada de IDs y nombres para autocompletar
            self.productos = [str(p[0]) for p in productos] + [p[1] for p in productos]
            completer = QCompleter(self.productos)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

            self.codigo_entrada.setCompleter(completer)
            self.codigo_salida.setCompleter(completer)
            self.nuevo_codigo.setCompleter(completer)

        except Exception as e:
            print("❌ Error al configurar autocompletado:", e)
            self.productos = []

    def crear_linea_separadora(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setFrameShadow(QFrame.Shadow.Sunken)
        return linea

    def crear_tab_entrada(self):
        layout = QVBoxLayout()

        self.codigo_entrada = QLineEdit()
        self.codigo_entrada.setPlaceholderText("ID o Nombre del Producto")
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
        self.codigo_salida.setPlaceholderText("ID o Nombre del Producto")
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
        self.nuevo_codigo.setPlaceholderText("ID del producto (dejar vacío para nuevo)")
        self.nuevo_codigo.editingFinished.connect(lambda: self.autocompletar("gestion"))

        self.nuevo_nombre = QLineEdit()
        self.nuevo_nombre.setPlaceholderText("Nombre del producto")

        self.nueva_unidad = QLineEdit()
        self.nueva_unidad.setPlaceholderText("Unidad de medida (KG, L, PZA)")

        self.nuevo_area = QLineEdit()
        self.nuevo_area.setPlaceholderText("Área (QUIMO o QUIMO CLEAN)")

        self.nuevo_estatus = QLineEdit()
        self.nuevo_estatus.setPlaceholderText("Estatus (true/false)")

        self.nuevo_precio = QLineEdit()
        self.nuevo_precio.setPlaceholderText("Precio de venta")

        self.label_info_gestion = QLabel("...")
        self.label_info_gestion.setWordWrap(True)

        btn_agregar = QPushButton("Agregar/Actualizar Producto")
        btn_agregar.clicked.connect(self.guardar_producto)

        btn_baja = QPushButton("Dar de baja producto")
        btn_baja.clicked.connect(self.dar_de_baja_producto)

        btn_multi = QPushButton("¿Actualizar varios?")
        btn_multi.clicked.connect(self.abrir_ventana_multiple)

        layout.addWidget(QLabel("Gestión de Productos"))
        layout.addWidget(self.nuevo_codigo)
        layout.addWidget(self.nuevo_nombre)
        layout.addWidget(self.nueva_unidad)
        layout.addWidget(self.nuevo_area)
        layout.addWidget(self.nuevo_estatus)
        layout.addWidget(self.nuevo_precio)

        layout.addWidget(btn_agregar)
        layout.addWidget(btn_baja)
        layout.addWidget(btn_multi)

        layout.addWidget(self.label_info_gestion)
        layout.addWidget(self.crear_linea_separadora())

        tab = QWidget()
        tab.setLayout(layout)
        self.configurar_autocompletado()
        return tab

    def abrir_ventana_multiple(self):
        dlg = VentanaActualizacionMultiple(self, productos=self.productos)
        dlg.exec()
        self.actualizar_tabla_callback()

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
            conn = self.get_db_connection()
            if not conn:
                return

            cursor = conn.cursor()
            
            # Intentar buscar por ID si es numérico
            if texto.isdigit():
                cursor.execute("""
                    SELECT id_producto, nombre_producto, unidad_medida_producto, 
                           area_producto, cantidad_producto, estatus_producto
                    FROM productos WHERE id_producto = %s
                """, (int(texto),))
            else:
                # Buscar por nombre si no es numérico
                cursor.execute("""
                    SELECT id_producto, nombre_producto, unidad_medida_producto, 
                           area_producto, cantidad_producto, estatus_producto
                    FROM productos WHERE nombre_producto ILIKE %s
                """, (f"%{texto}%",))
            
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                id_producto, nombre, unidad, area, cantidad, estatus = resultado

                if destino == "entrada":
                    self.label_info_entrada.setText(f"{nombre} | Stock: {cantidad} {unidad}")
                    self.codigo_entrada.setText(str(id_producto))  # Establecer el ID
                elif destino == "salida":
                    self.label_info_salida.setText(f"{nombre} | Stock: {cantidad} {unidad}")
                    self.codigo_salida.setText(str(id_producto))  # Establecer el ID
                elif destino == "gestion":
                    self.nuevo_codigo.setText(str(id_producto))
                    self.nuevo_nombre.setText(nombre)
                    self.nueva_unidad.setText(unidad)
                    self.nuevo_area.setText(area)
                    self.nuevo_estatus.setText(str(estatus))
                    # Nota: No hay precio en la consulta básica, puedes agregarlo si es necesario
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

        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            cursor = conn.cursor()
            
            # Intentar buscar por ID si es numérico
            if texto.isdigit():
                cursor.execute("""
                    SELECT id_producto, nombre_producto, cantidad_producto 
                    FROM productos WHERE id_producto = %s
                """, (int(texto),))
            else:
                # Buscar por nombre si no es numérico
                cursor.execute("""
                    SELECT id_producto, nombre_producto, cantidad_producto 
                    FROM productos WHERE nombre_producto ILIKE %s
                """, (texto,))
            
            resultado = cursor.fetchone()

            if not resultado:
                QMessageBox.critical(self, "Error", "Producto no encontrado.")
                return

            id_producto, nombre, stock_actual = resultado
            nuevo_stock = stock_actual + cantidad if tipo == "entrada" else stock_actual - cantidad

            if nuevo_stock < 0:
                QMessageBox.critical(self, "Error", "No hay suficiente stock.")
                return

            # Actualizar stock
            cursor.execute("""
                UPDATE productos 
                SET cantidad_producto = %s 
                WHERE id_producto = %s
            """, (nuevo_stock, id_producto))

            # Registrar movimiento
            tabla = "entradas" if tipo == "entrada" else "salidas"
            cursor.execute(f"""
                INSERT INTO {tabla} (producto_id, cantidad, fecha)
                VALUES (%s, %s, NOW())
            """, (id_producto, cantidad))

            conn.commit()
            self.actualizar_tabla_callback()
            QMessageBox.information(self, "Éxito", f"{tipo.title()} registrada correctamente.")
            self.limpiar_formulario(tipo)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de base de datos:\n{e}")
        finally:
            if conn:
                conn.close()

    def limpiar_formulario(self, tipo):
        if tipo == "entrada":
            self.codigo_entrada.clear()
            self.cantidad_entrada.clear()
            self.label_info_entrada.setText("...")
        elif tipo == "salida":
            self.codigo_salida.clear()
            self.cantidad_salida.clear()
            self.label_info_salida.setText("...")
        elif tipo == "gestion":
            self.nuevo_codigo.clear()
            self.nuevo_nombre.clear()
            self.nueva_unidad.clear()
            self.nuevo_area.clear()
            self.nuevo_estatus.clear()
            self.nuevo_precio.clear()
            self.label_info_gestion.setText("...")

    def guardar_producto(self):
        datos = {
            "id": self.nuevo_codigo.text().strip(),
            "nombre": self.nuevo_nombre.text().strip(),
            "unidad": self.nueva_unidad.text().strip(),
            "area": self.nuevo_area.text().strip(),
            "estatus": self.nuevo_estatus.text().strip().lower() == 'true',
            "precio": self.nuevo_precio.text().strip()
        }

        # Validaciones básicas
        if not datos["nombre"] or not datos["unidad"] or not datos["area"]:
            QMessageBox.warning(self, "Campos incompletos", "Nombre, unidad y área son obligatorios.")
            return

        try:
            datos["precio"] = float(datos["precio"]) if datos["precio"] else 0.0
        except ValueError:
            QMessageBox.warning(self, "Precio inválido", "El precio debe ser un número.")
            return

        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            cursor = conn.cursor()
            
            if datos["id"]:  # Actualización de producto existente
                try:
                    producto_id = int(datos["id"])
                    cursor.execute("""
                        UPDATE productos
                        SET nombre_producto = %s,
                            unidad_medida_producto = %s,
                            area_producto = %s,
                            estatus_producto = %s,
                            precio_venta = %s
                        WHERE id_producto = %s
                    """, (
                        datos["nombre"], datos["unidad"], datos["area"],
                        datos["estatus"], datos["precio"], producto_id
                    ))
                except ValueError:
                    QMessageBox.warning(self, "ID inválido", "El ID del producto debe ser un número.")
                    return
            else:  # Nuevo producto
                cursor.execute("""
                    INSERT INTO productos (
                        nombre_producto, unidad_medida_producto, 
                        area_producto, estatus_producto, precio_venta
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    datos["nombre"], datos["unidad"], datos["area"],
                    datos["estatus"], datos["precio"]
                ))

            conn.commit()
            QMessageBox.information(self, "Éxito", "Producto guardado correctamente.")
            self.limpiar_formulario("gestion")
            self.configurar_autocompletado()
            self.actualizar_tabla_callback()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el producto:\n{e}")
        finally:
            if conn:
                conn.close()

    def dar_de_baja_producto(self):
        id_producto = self.nuevo_codigo.text().strip()
        if not id_producto:
            QMessageBox.warning(self, "ID vacío", "Escribe el ID del producto.")
            return

        try:
            producto_id = int(id_producto)
        except ValueError:
            QMessageBox.warning(self, "ID inválido", "El ID debe ser un número.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar baja",
            f"¿Dar de baja el producto con ID {producto_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            conn = None
            try:
                conn = self.get_db_connection()
                if not conn:
                    return

                cursor = conn.cursor()
                
                # Opción 1: Eliminar físicamente
                # cursor.execute("DELETE FROM productos WHERE id_producto = %s", (producto_id,))
                
                # Opción 2: Marcar como inactivo (recomendado)
                cursor.execute("""
                    UPDATE productos 
                    SET estatus_producto = false 
                    WHERE id_producto = %s
                """, (producto_id,))
                
                cambios = cursor.rowcount
                conn.commit()

                if cambios:
                    QMessageBox.information(self, "Éxito", "Producto dado de baja.")
                    self.limpiar_formulario("gestion")
                    self.configurar_autocompletado()
                    self.actualizar_tabla_callback()
                else:
                    QMessageBox.information(self, "No encontrado", "No se encontró el producto.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo dar de baja:\n{e}")
            finally:
                if conn:
                    conn.close()