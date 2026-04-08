import unittest
import sqlite3
import os  # Importante para poder borrar el archivo
from Inventario import Producto, Inventario

class TestInventario(unittest.TestCase):

    def setUp(self):
        """Configuración inicial: base de datos temporal en disco para cada test"""
        self.inv = Inventario()
        # En lugar de :memory:, usamos un archivo de prueba
        self.inv.archivo_db = "test_db.db"
        self.inv.crear_tabla()

    def tearDown(self):
        """Se ejecuta al final de cada test para borrar la BD de prueba y dejar todo limpio"""
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")

    def test_crear_producto_valido(self):
        """Verifica la creación de un producto con datos correctos"""
        p = Producto("001", "Laptop", "Tecnología", 1200.50, 10)
        self.assertEqual(p.nombre, "laptop")
        self.assertEqual(p.precio, 1200.50)

    def test_error_precio_negativo(self):
        """Verifica que lance ValueError con precio negativo"""
        with self.assertRaises(ValueError):
            Producto("001", "Error", "Test", -10, 5)

    def test_agregar_y_buscar_producto(self):
        """Prueba la inserción y recuperación en SQLite"""
        p = Producto("A1", "Teclado", "Perifericos", 25.0, 5)
        self.inv.agregar_producto(p)
        
        resultado = self.inv.buscar_producto_por_id("A1")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.nombre, "teclado")

    def test_quitar_stock_insuficiente(self):
        """Verifica la protección de stock negativo en SQL"""
        p = Producto("B1", "Mouse", "Perifericos", 10.0, 5)
        self.inv.agregar_producto(p)
        
        # Intentamos quitar 10 teniendo solo 5
        self.inv.quitar_stock("B1", 10)
        
        # El stock debe seguir siendo 5 (la query debió fallar por el WHERE cantidad >= ?)
        resultado = self.inv.buscar_producto_por_id("B1")
        self.assertEqual(resultado.cantidad, 5)

    def test_eliminar_producto(self):
        """Verifica que el borrado funcione correctamente"""
        p = Producto("D1", "Borrar", "Test", 1.0, 1)
        self.inv.agregar_producto(p)
        self.inv.eliminar_producto("D1")
        
        resultado = self.inv.buscar_producto_por_id("D1")
        self.assertIsNone(resultado)

# ESTO ES LO QUE FALTABA: El punto de entrada para ejecutar los tests
if __name__ == "__main__":
    unittest.main()