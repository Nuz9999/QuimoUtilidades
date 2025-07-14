from PyQt6.QtWidgets import QApplication
import sys
from ui.ui_inventario import InventarioApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = InventarioApp()
    ventana.show()
    sys.exit(app.exec())



# uTILIDAD BRUTA - UTILIDAD NETA - GASTOS DE OPERACIÓN - GASTOS FINANCIEROS - IMPUESTOS = UTILIDAD NETA
# UTILIDAD BRUTA - GASTOS DE OPERACIÓN = UTILIDAD DE OPERACIÓN