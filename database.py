import os
import json
import psycopg2
from PyQt6.QtWidgets import QMessageBox

class DatabaseManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.config_path = os.path.join(os.path.dirname(__file__), 'db_config.json')
        self.config = self.load_config()

    def load_config(self):
        """Carga la configuración desde el archivo JSON"""
        if not os.path.exists(self.config_path):
            self.create_default_config()
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self.parent, "Error de configuración", 
                                f"No se pudo leer el archivo de configuración:\n{e}")
            return self.create_default_config()

    def create_default_config(self):
        """Crea una configuración por defecto si no existe"""
        default_config = {
            "host": "localhost",
            "port": "5432",
            "dbname": "quimoBD",
            "user": "postgres",
            "password": "postgres"
        }
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        except Exception as e:
            QMessageBox.critical(self.parent, "Error crítico", 
                                f"No se pudo crear el archivo de configuración:\n{e}")
            return default_config

    def get_connection(self):
        """Establece conexión con la base de datos PostgreSQL"""
        try:
            conn = psycopg2.connect(
                dbname=self.config['dbname'],
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port'],
                connect_timeout=5
            )
            return conn
        except Exception as e:
            QMessageBox.critical(self.parent, "Error de conexión", 
                                f"No se pudo conectar a la base de datos:\n{e}\n\n"
                                f"Verifique la configuración en:\n{self.config_path}")
            return None

    def test_connection(self):
        """Prueba la conexión y devuelve True si es exitosa"""
        conn = self.get_connection()
        if conn:
            conn.close()
            return True
        return False