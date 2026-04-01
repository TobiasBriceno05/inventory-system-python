# Sistema de inventario en consola (Python + JSON)

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JSON](https://img.shields.io/badge/Persistencia-JSON-000000?style=for-the-badge&logo=json&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-unittest-169b62?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Aplicación de **línea de comandos** para gestionar un inventario de productos con **Programación Orientada a Objetos**, **validación en capas** y **persistencia** en `BaseDeDatos.json`. Incluye **pruebas unitarias** con `unittest` para asegurar reglas de negocio y facilitar refactorización con confianza.

---

## Tabla de contenidos

| Sección | Contenido |
|---------|-----------|
| [Arquitectura](#arquitectura-de-software) | POO, capas y defensa en profundidad |
| [Robustez](#robustez-y-manejo-de-errores) | Excepciones, duplicados, precios |
| [Algoritmos](#eficiencia-algorítmica) | Diccionarios y complejidad |
| [Testing](#fase-de-testing) | Cómo ejecutar y por qué importa |
| [Uso](#instrucciones-de-uso) | Flujo actual campo a campo |
| [Estructura](#estructura-del-repositorio) | Archivos del proyecto |
| [Roadmap](#próximos-pasos) | Fase 2 con SQLite |

---

## Arquitectura de software

El diseño separa **modelo de dominio**, **servicio de persistencia** (implícito en `Inventario`) y **interfaz de usuario** (consola), manteniendo el núcleo reutilizable y testeable.

| Componente | Rol |
|------------|-----|
| `Producto` | Entidad: identidad (`id`), atributos normalizados (`nombre`, `categoria` en minúsculas) y `precio` numérico. |
| `Inventario` | Agregado: colección en memoria, carga/guardado JSON, reglas de unicidad por `id`. |
| `solicitar_datos_producto` / `menu` | Presentación: lectura interactiva y orquestación del flujo. |

### Defensa en profundidad (validación en capas)

La **defensa en profundidad** aplica reglas tanto en la **UI** como en el **modelo/capa de dominio**, de modo que el sistema siga siendo coherente aunque en el futuro se reutilice `Producto` o `Inventario` desde otra interfaz (API, GUI, scripts).

| Capa | Qué valida | Dónde en código |
|------|------------|-----------------|
| **Interfaz (UI)** | ID no vacío, ID no duplicado respecto al inventario cargado, precio numérico y no negativo (reintento amigable). | `solicitar_datos_producto` |
| **Modelo** | Precio no negativo al construir el objeto (*fail-fast* con `ValueError`). | `Producto.__init__` |
| **Servicio / inventario** | Imposibilidad de insertar un segundo producto con el mismo `id` (integridad del almacén). | `Inventario.agregar` |

Así, una entrada maliciosa o un bug en la consola **no basta** para violar invariantes: la capa de dominio sigue rechazando estados inválidos.

---

## Robustez y manejo de errores

| Escenario | Estrategia |
|-----------|------------|
| **Archivo JSON ausente** | `Inventario.cargar()` captura `FileNotFoundError` e inicializa un inventario vacío; primera ejecución sin crash. |
| **Precio no numérico en consola** | `try` / `except ValueError` al convertir con `float()`; mensaje claro y nuevo intento sin cerrar el programa. |
| **Precio negativo** | Validación en UI (bucle) y, además, `ValueError` en `Producto` si se instanciara con datos incorrectos desde código o tests. |
| **ID duplicado** | Comprobación en `solicitar_datos_producto` y refuerzo con `ValueError` en `agregar` si el `id` ya existe. |

Este enfoque reduce **caídas abruptas** por entradas de usuario incorrectas y documenta **contratos explícitos** (excepciones) para quien integre o extienda el módulo.

---

## Eficiencia algorítmica

Los productos viven en un **`dict`** de Python cuya clave es el **ID del producto**. Internamente, el diccionario se implementa como **tabla hash**, lo que implica:

| Operación | Complejidad (caso medio) | Motivo |
|-----------|---------------------------|--------|
| Comprobar si existe un `id` | **O(1)** | Acceso por clave en tabla hash. |
| Alta / baja por `id` | **O(1)** | Inserción y borrado por clave. |
| Búsqueda por **nombre** | **O(n)** | `buscar` recorre los valores hasta coincidencia (no hay índice secundario por nombre). |

El modelo prioriza el **ID como clave de negocio** para operaciones críticas en tiempo constante; la búsqueda por nombre es adecuada para volúmenes modestos y consola educativa.

---

## Fase de testing

El archivo `test_inventario.py` define una suite **`unittest`** que verifica el comportamiento del dominio sin depender de interacción manual.

### Cómo ejecutar las pruebas

Desde la carpeta del proyecto:

```bash
python -m unittest test_inventario.py -v
```

Equivalente:

```bash
python test_inventario.py
```

### Qué cubren los tests

| Test | Objetivo |
|------|----------|
| `test_agregar_producto_valido` | Alta correcta y normalización de `nombre` a minúsculas. |
| `test_error_precio_negativo` | `Producto` rechaza precios negativos con `ValueError`. |
| `test_error_id_duplicado` | `agregar` no permite dos productos con el mismo `id`. |
| `test_eliminar_existente` | Eliminación actualiza el estado en memoria. |

### Aislamiento y datos reales

Antes de cada caso, el inventario de prueba redirige la persistencia a **`BaseDeDatos_test.json`** y limpia la colección en memoria; **`tearDown`** elimina ese archivo si existe. Así las pruebas **no sobrescriben** tu `BaseDeDatos.json` de trabajo.

### Por qué importa

Las pruebas automatizadas actúan como **especificación ejecutable**: cualquier cambio futuro (por ejemplo, migración a SQLite) puede comprobar que las reglas de negocio se mantienen. Detectan regresiones de forma **rápida y repetible**, esencial en un portafolio que demuestra **ingeniería**, no solo scripts puntuales.

---

## Instrucciones de uso

### Requisitos

- [Python 3.x](https://www.python.org/downloads/) en el `PATH`.
- Solo biblioteca estándar: `json`, `unittest`, `os`.

### Ejecutar la aplicación

```bash
python Inventario.py
```

El punto de entrada está protegido con `if __name__ == "__main__":`, de modo que al importar el módulo desde los tests **no** se abre el menú automáticamente.

### Flujo del menú

```text
--- SISTEMA DE INVENTARIO ---
1. Agregar Producto
2. Eliminar Producto
3. Buscar por Nombre
4. Mostrar Todo
5. Salir
```

### Alta de producto (entrada por campos)

A diferencia de un único renglón separado por espacios, cada dato se pide **por separado**. Eso permite nombres y categorías con **espacios internos**, por ejemplo:

```text
Ingrese el ID del producto: SKU-IPH17P
Ingrese el nombre del producto: iPhone 17 Pro
Ingrese la categoria del producto: telefonia movil
Ingrese el precio del producto: 1299.99
```

| Opción | Comportamiento |
|--------|----------------|
| **1 — Agregar** | Bucle para ID válido y único; luego nombre, categoría y precio (con reintentos si el precio no es número o es negativo). |
| **2 — Eliminar** | Solicita `id`; confirma existencia antes de borrar y persistir. |
| **3 — Buscar** | Por nombre (comparación en minúsculas); muestra ficha resumida si hay coincidencia. |
| **4 — Mostrar todo** | Tabla con IDs, nombres y categorías en mayúsculas de presentación y precio formateado. |
| **5 — Salir** | Cierra el programa; los datos ya guardados permanecen en JSON. |

Si `BaseDeDatos.json` no existe, el arranque es con inventario vacío y el archivo se crea al primer guardado.

---

## Estructura del repositorio

```text
INVENTARIO/
├── Inventario.py         # Modelo, inventario, I/O JSON, menú y solicitud de datos
├── test_inventario.py    # Pruebas unitarias (unittest)
├── BaseDeDatos.json      # Persistencia local (omitida del control de versiones si está en .gitignore)
└── README.md
```

---

## Próximos pasos

| Fase | Objetivo |
|------|----------|
| **Fase 2 (planeada)** | **Migración a base de datos relacional** con **SQLite**: esquema tabular, consultas SQL, transacciones y evolución hacia un modelo de datos más escalable sin renunciar a dependencias mínimas (SQLite en la biblioteca estándar vía `sqlite3`). |

---

## Licencia

Este proyecto puede distribuirse bajo la licencia **MIT** (ajusta este apartado si el repositorio usa otra licencia).

---

<p align="center">
  <sub>Portafolio académico · Ciencias de la Computación</sub>
</p>
