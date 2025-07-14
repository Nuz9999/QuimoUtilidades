from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt


class PanelInferior(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(self.crear_linea_separadora())
        layout.addWidget(QLabel("<b>Panel Inferior</b>"))

        # Labels
        self.label_precio = QLabel("Precio unitario: -")
        self.label_moneda = QLabel("Moneda: MXN")
        self.label_bruto = QLabel("Bruto: -")
        self.label_neto = QLabel("Neto: -")

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.label_precio)
        h_layout.addStretch()
        h_layout.addWidget(self.label_moneda)
        h_layout.addStretch()
        h_layout.addWidget(self.label_bruto)
        h_layout.addStretch()
        h_layout.addWidget(self.label_neto)

        layout.addLayout(h_layout)
        self.setLayout(layout)

    def crear_linea_separadora(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setFrameShadow(QFrame.Shadow.Sunken)
        return linea

    def calcular_y_actualizar(self, precio_unitario, cantidad, moneda="MXN"):
        """
        Calcula y actualiza los valores mostrados en el panel inferior.

        :param precio_unitario: precio por unidad (float)
        :param cantidad: cantidad comprada (float)
        :param moneda: moneda, por defecto MXN
        """
        try:
            bruto = float(precio_unitario) * float(cantidad)
            neto = bruto * 1.16
        except Exception:
            bruto = 0.0
            neto = 0.0

        self.label_precio.setText(f"Precio unitario: {precio_unitario:.2f}")
        self.label_moneda.setText(f"Moneda: {moneda}")
        self.label_bruto.setText(f"Bruto: {bruto:.2f}")
        self.label_neto.setText(f"Neto: {neto:.2f}")
