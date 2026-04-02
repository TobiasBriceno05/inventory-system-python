import unittest
import os
import json
from Inventario import Inventario, Producto

class TestSistemaInventario(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada test. Crea un entorno limpio."""
        self.archivo_test = "BaseDeDatos_test.json"
        # Forzamos al inventario a usar un archivo de pruebas para no borrar tus datos reales
        self.inventario = Inventario()
        self.inventario.archivo = self.archivo_test
        self.inventario.productos = {}

    def tearDown(self):
        """Se ejecuta después de cada test. Limpia el archivo de pruebas."""
        if os.path.exists(self.archivo_test):
            os.remove(self.archivo_test)

    def test_agregar_producto_valido(self):
        """Prueba que un producto correcto se guarde en el diccionario."""
        p = Producto("TEMP01", "Test Item", "Pruebas", 10.50)
        self.inventario.agregar(p)
        self.assertIn("TEMP01", self.inventario.productos)
        self.assertEqual(self.inventario.productos["TEMP01"].nombre, "test item")

    def test_error_precio_negativo(self):
        """Prueba que el sistema explote (excepción) si el precio es negativo."""
        with self.assertRaises(ValueError):
            Producto("ERR01", "Invalido", "Falla", -5.0)

    def test_error_id_duplicado(self):
        """Prueba que el método agregar bloquee IDs repetidos."""
        p1 = Producto("DBL01", "Original", "Cat", 10.0)
        p2 = Producto("DBL01", "Copia", "Cat", 20.0)
        
        self.inventario.agregar(p1)
        # Aquí verificamos que el último cambio en 'agregar' funcione:
        with self.assertRaises(ValueError):
            self.inventario.agregar(p2)

    def test_eliminar_existente(self):
        """Prueba que eliminar realmente borre del diccionario."""
        p = Producto("DEL01", "Borrar", "Cat", 5.0)
        self.inventario.agregar(p)
        self.inventario.eliminar("DEL01")
        self.assertNotIn("DEL01", self.inventario.productos)

if __name__ == "__main__":
    unittest.main()