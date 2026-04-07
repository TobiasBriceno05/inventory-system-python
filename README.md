# 📦 Sistema Versátil de Gestión de Inventarios (Python + JSON)

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JSON](https://img.shields.io/badge/Persistencia-JSON-000000?style=for-the-badge&logo=json&logoColor=white)
![Status](https://img.shields.io/badge/Fase-1%20(Completada)-success?style=for-the-badge)
![Testing](https://img.shields.io/badge/Tests-unittest-169b62?style=for-the-badge&logo=python&logoColor=white)

Motor de gestión de existencias de propósito general, desarrollado bajo principios de **Programación Orientada a Objetos (POO)**. Este sistema proporciona una infraestructura robusta para el control de activos, permitiendo su adaptación a cualquier sector (comercio, tecnología, suministros médicos o ferretería) mediante una arquitectura basada en identificadores únicos (IDs).

---

## 🚀 Funcionalidades Universales

| Módulo | Descripción Técnica |
| :--- | :--- |
| **Control de Stock Dinámico** | Gestión de cantidades con lógica de prevención de inventario negativo y validación de integridad. |
| **Transacciones de Almacén** | Flujos de entrada (abastecimiento) y salida (consumo/venta) optimizados mediante búsqueda por ID. |
| **Valoración de Activos** | Cálculo automatizado del valor total de la mercancía basado en el coste unitario y existencias actuales. |
| **Reportes Analíticos** | Visualización de datos en formato tabular con indicadores de stock crítico para reposición. |
| **Capa de Persistencia** | Serialización de datos en JSON con mecanismos de recuperación ante archivos vacíos o corruptos. |

---

## 🏗️ Arquitectura del Software

El sistema implementa una separación de responsabilidades para garantizar la escalabilidad:

1.  **Modelo (`Producto`):** Entidad encargada de la validación de reglas de negocio atómicas (precio, cantidad y formato de datos).
2.  **Lógica (`Inventario`):** Controlador de alto nivel que gestiona el estado de los datos en memoria y coordina la persistencia en disco.
3.  **Interfaz (`CLI`):** Capa de interacción que abstrae la complejidad técnica al usuario, gestionando excepciones para mantener la estabilidad del proceso.

---

## 📊 Eficiencia Algorítmica

El núcleo del sistema utiliza **Tablas Hash (Diccionarios)** para garantizar que el rendimiento no se degrade con el volumen de datos:

* **Acceso/Búsqueda por ID:** $O(1)$ - Tiempo constante.
* **Inserción y Actualización:** $O(1)$ - Sin necesidad de iteraciones.
* **Eliminación:** $O(1)$ - Remoción directa por clave.
* **Cálculo de Activos:** $O(n)$ - Recorrido lineal optimizado.

---

## 🛠️ Instalación y Uso

### Requisitos
* Python 3.10 o superior.
* Sin dependencias externas (Standard Library).

### Ejecución
```bash
python Inventario.py
Flujo de Trabajo Versátil
El sistema se adapta a cualquier inventario mediante este ciclo:

Catalogar: Registre el producto/activo por primera vez (Opción 1.1).

Ingresar: Aumente las unidades cuando reciba nuevos suministros (Opción 1.2).

Egresar: Reduzca el stock tras una venta, uso o retiro del almacén (Opción 2.2).

Auditar: Visualice el estado actual y valor monetario del inventario (Opción 4).

🧪 Suite de Pruebas
Para garantizar que los cambios futuros (como la migración a SQL) no rompan la lógica actual, se incluye una batería de tests unitarios:

Bash
python -m unittest test_inventario.py
🗺️ Roadmap: Hacia la Fase 2
[ ] Motor Relacional: Migración de almacenamiento JSON a SQLite para soporte de transacciones complejas.

[ ] Historial de Movimientos: Implementación de logs para auditoría de entradas y salidas.

[ ] Búsqueda Avanzada: Filtros dinámicos por categorías o rangos de precios.

<p align="center">
<sub>Proyecto Académico de Ciencias de la Computación (UCV)</sub>
</p>