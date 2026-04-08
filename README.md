# 📦 OmniStock: Sistema de Gestión de Inventarios con SQLite

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Estado-Producción_Lista-success?style=for-the-badge)

**OmniStock** es una solución de consola de alto rendimiento para el control de existencias, migrada de una arquitectura estática a un motor relacional basado en **SQLite3**. Diseñada bajo principios de **Programación Orientada a Objetos (POO)**, la aplicación garantiza la persistencia real de los datos y una integridad lógica superior.

---

## 🚀 Características Principales

* **Persistencia Relacional:** Implementación completa con SQLite3 para el almacenamiento persistente, eliminando la volatilidad de datos.
* **Arquitectura Robusta (POO):** Modelado basado en clases (`Producto`, `Inventario`) que facilita la escalabilidad del código.
* **Manejo de Errores por Capas:** * *Capa de Interfaz:* Validación de tipos de entrada para prevenir cierres inesperados.
    * *Capa de Lógica:* Protecciones a nivel de base de datos para evitar stocks negativos o inconsistencias.
* **Gestión Masiva:** Motor de actualización de precios por categorías y generación de reportes de stock bajo.
* **Visualización Profesional:** Tablas formateadas en consola para una auditoría rápida de activos.

---

## 🏛️ Arquitectura del Sistema

El proyecto sigue una separación de responsabilidades clara para mantener un código limpio y mantenible:

1.  **Modelo de Datos (`Producto`):** Clase que encapsula las propiedades del objeto y realiza las validaciones de negocio iniciales (Fail-fast).
2.  **Controlador de Persistencia (`Inventario`):** Gestiona la conexión con el motor SQLite, las consultas SQL parametrizadas y la integridad de la base de datos.
3.  **Interfaz de Usuario (`Menu`):** Capa encargada de la interacción con el usuario, sanitizando las entradas antes de enviarlas al controlador.

---

## 🛠️ Tecnologías

* **Lenguaje:** Python 3.x
* **Base de Datos:** SQLite3 (Motor relacional embebido)
* **Librerías:** Uso exclusivo de la **Standard Library** (sin dependencias externas).

---

## 💻 Instalación y Uso

Al no requerir dependencias externas, la puesta en marcha es inmediata:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/nombre-del-repo.git](https://github.com/tu-usuario/nombre-del-repo.git)
    cd nombre-del-repo
    ```

2.  **Ejecutar la aplicación:**
    ```bash
    python Inventario.py
    ```

### Ejemplo de Visualización
El sistema genera tablas legibles directamente en la consola:
```text
+--------+-----------------+--------------+----------+-------+
| ID     | PRODUCTO        | CATEGORÍA    | PRECIO   | STOCK |
+--------+-----------------+--------------+----------+-------+
| TECH01 | Laptop Pro      | Tecnología   | $1200.00 |   15  |
| PERI05 | Mouse Gamer     | Periféricos  | $45.50   |    3  |
+--------+-----------------+--------------+----------+-------+
[ALERTA]: El producto 'Mouse Gamer' está por debajo del límite de stock.
🧪 Suite de Pruebas
Para garantizar la fiabilidad del sistema, se incluye una batería de pruebas unitarias que validan desde la creación de tablas hasta la lógica de transacciones:

Bash
python -m unittest test_inventario.py
✒️ Autor
Tobias Briceño – Desarrollador Principal – Estudiante de Computación en la Universidad Central de Venezuela (UCV).