# Python Inventory System with JSON Persistence

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JSON](https://img.shields.io/badge/Data-JSON-000000?style=for-the-badge&logo=json&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Sistema de consola que gestiona un **inventario de productos** mediante **Programación Orientada a Objetos** (clases `Producto` e `Inventario`). Los datos **persisten en disco** en `BaseDeDatos.json`, de modo que el estado sobrevive entre ejecuciones sin depender solo de la memoria del proceso.

---

## Características clave

| Área | Detalle |
|------|---------|
| **CRUD** | Alta (`agregar`), baja (`eliminar`), consulta por nombre (`buscar`) y listado completo (`Mostrar Todo`). |
| **Normalización** | `nombre` y `categoria` se almacenan en **minúsculas** para comparaciones consistentes. |
| **Salida tabular** | Listado alineado en consola con separadores y formato monetario (`$` y dos decimales). |
| **Persistencia** | Lectura al iniciar y escritura tras cada modificación mediante el módulo `json`. |

---

## Análisis técnico

- **Diccionario como índice principal**  
  Los productos se guardan en `self.productos` con el **ID como clave**. Eso permite **inserción, borrado y comprobación de existencia por ID** con complejidad **O(1)** en el caso medio (tabla hash de Python).  
  La búsqueda **por nombre** recorre los valores del diccionario (**O(n)**), coherente con un modelo donde el identificador es la clave natural del almacén.

- **Manejo de excepciones en la carga**  
  `cargar()` envuelve la apertura y `json.load()` en un `try/except`. Si el archivo no existe (`FileNotFoundError`), se inicializa un inventario vacío en lugar de fallar, lo que mejora la **primera ejecución** y la **robustez** ante rutas o despliegues nuevos.

- **Separación de responsabilidades**  
  `Producto.to_dict()` serializa el objeto; `Inventario` concentra I/O y la colección en memoria.

---

## Requisitos

- [Python 3.x](https://www.python.org/downloads/) instalado y disponible en el `PATH`.

No se requieren dependencias externas: solo la biblioteca estándar (`json`).

---

## Instrucciones de uso

1. Clona o descarga el repositorio y colócate en la carpeta del proyecto.

2. Ejecuta el script desde una terminal:

```bash
python Inventario.py
```

3. Verás un menú interactivo. Ejemplo de flujo:

```text
--- SISTEMA DE INVENTARIO ---
1. Agregar Producto
2. Eliminar Producto
3. Buscar por Nombre
4. Mostrar Todo
5. Salir
```

- **Agregar (1):** introduce **ID, nombre, categoría y precio** separados por espacios (cuatro tokens). Ejemplo: `SKU01 laptop electronica 899.99`  
- **Eliminar (2):** introduce el **ID** del producto.  
- **Buscar (3):** introduce el **nombre** (se compara en minúsculas).  
- **Mostrar todo (4):** imprime la tabla con todos los registros cargados desde JSON.  
- **Salir (5):** termina el programa; los datos ya guardados permanecen en `BaseDeDatos.json`.

Si el archivo JSON no existe, el programa arranca con inventario vacío y lo creará al primer guardado.

---

## Estructura del proyecto (referencia)

```text
INVENTARIO/
├── Inventario.py      # Lógica POO, menú y persistencia
├── BaseDeDatos.json   # Datos persistidos (generado/actualizado en runtime)
└── README.md
```

---

## Aprendizajes

Venir de **C++** acostumbra a pensar en **gestión explícita de memoria**, punteros y el ciclo de vida de los objetos al pie de la letra. En **Python**, la asignación y la recolección de basura automatizan gran parte de ese trabajo: el foco pasa a **modelar bien los datos** (por ejemplo, un `dict` indexado por ID), a **contratos claros entre capas** (objeto ↔ JSON) y a **errores previsibles** (archivo ausente, formato de entrada incorrecto). Este proyecto fue un primer paso sólido para internalizar ese cambio de mentalidad sin renunciar a rigor algorítmico ni a código legible.

---

## Licencia

Este proyecto puede distribuirse bajo la licencia **MIT** (ajusta este apartado si usas otra licencia en el repositorio).

---

<p align="center">
  <sub>Proyecto académico · Ciencias de la Computación</sub>
</p>
