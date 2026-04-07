# 🛒 Sistema de Gestión de Inventario para Bodegón

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JSON](https://img.shields.io/badge/Persistencia-JSON-000000?style=for-the-badge&logo=json&logoColor=white)
![Status](https://img.shields.io/badge/Fase-1%20(Completada)-success?style=for-the-badge)
![Testing](https://img.shields.io/badge/Tests-unittest-169b62?style=for-the-badge&logo=python&logoColor=white)

Software de línea de comandos para la gestión profesional de existencias, diseñado bajo principios de **Programación Orientada a Objetos (POO)** y **Defensa en Profundidad**. Esta versión está optimizada para el flujo de trabajo de un bodegón, permitiendo el control de entradas, salidas y valoración de activos.

---

## 🚀 Funcionalidades Principales

| Módulo | Descripción |
| :--- | :--- |
| **Gestión de Stock** | Control de cantidades por producto con validación de stock mínimo y prevención de valores negativos. |
| **Entradas y Salidas** | Submenús especializados para crear nuevos SKUs o reabastecer productos existentes por ID. |
| **Análisis Financiero** | Cálculo automático del valor total del inventario ($\sum precio \times cantidad$). |
| **Reportes Visuales** | Visualización tabular alineada con alertas automáticas de **Bajo Stock** (< 5 unidades). |
| **Persistencia Robusta** | Almacenamiento en JSON con manejo de errores para archivos vacíos o corruptos. |

---

## 🏗️ Arquitectura del Sistema

El proyecto se divide en tres capas lógicas para asegurar la integridad de los datos:

1.  **Capa de Dominio (Modelo):** La clase `Producto` es la única responsable de validar que un precio o cantidad no nazca muerto (negativo).
2.  **Capa de Lógica (Controlador):** La clase `Inventario` gestiona el estado en memoria y asegura que cada cambio se sincronice con el almacenamiento.
3.  **Capa de Interfaz (Vista):** El menú captura excepciones de tipo `ValueError` y `KeyError`, evitando que errores de usuario cierren el programa.

---

## 📊 Eficiencia y Algoritmos

Al utilizar diccionarios de Python (Hash Maps) indexados por el **ID del Producto**, el sistema garantiza una velocidad constante independientemente del tamaño del inventario.

* **Búsqueda por ID:** $O(1)$ - Instantánea.
* **Actualización de Stock:** $O(1)$ - Sin necesidad de recorrer listas.
* **Eliminación:** $O(1)$ - Acceso directo a la clave.
* **Cálculo de Total:** $O(n)$ - Un único recorrido lineal.



---

## 🛠️ Instalación y Uso

### Requisitos
* Python 3.10 o superior.
* No requiere dependencias externas (Standard Library).

### Ejecución
```bash
python Inventario.py
Flujo de Trabajo Recomendado
Registrar: Use la opción 1.1 para meter un producto nuevo al catálogo.

Reabastecer: Use la opción 1.2 cuando llegue mercancía nueva de un producto ya registrado.

Vender: Use la opción 2.2 para descontar unidades del stock tras una venta.

Auditar: Use la opción 4 para ver el valor monetario de su bodega.

🧪 Testing
El proyecto incluye una suite de pruebas unitarias para garantizar que las reglas de negocio se cumplan siempre.
Para ejecutar los tests:

Bash
python -m unittest test_inventario.py
🗺️ Roadmap: Hacia la Fase 2
La estructura actual ha sido diseñada para facilitar la migración al siguiente nivel:

[ ] Migración a SQLite: Reemplazar el motor JSON por una base de datos relacional.

[ ] Historial de Transacciones: Tabla de logs para rastrear quién y cuándo modificó el stock.

[ ] Exportación a PDF: Generación de reportes de inventario y facturas simples.

<p align="center">
<sub>Desarrollado como proyecto académico - Ciencias de la Computación (UCV)</sub>
</p>