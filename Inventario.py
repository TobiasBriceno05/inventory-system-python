import sqlite3

class Producto:
    def __init__(self, id_prod, nombre, categoria, precio, cantidad=0):
        if precio < 0:
            raise ValueError("El precio no puede ser negativo") # Fail-fast
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa")
        self.id = id_prod
        self.nombre = nombre.lower()
        self.categoria = categoria.lower()
        self.precio = precio
        self.cantidad = cantidad # Si no se proporciona una cantidad, se establece en 0
    def to_dict(self):
        return {"id" : self.id, "nombre" : self.nombre, "categoria" : self.categoria, "precio" : self.precio, "cantidad" : self.cantidad}

class Inventario:
    def __init__(self):
        self.archivo_db = "BaseDeDatos.db"
        self.crear_tabla()

    def conectar(self):
        #Crea el 'puente' hacia la base de datos.
        return sqlite3.connect(self.archivo_db) 

    def crear_tabla(self): #Define la estructura de la tabla si el archivo es nuevo.
        conexion = self.conectar()
        cursor = conexion.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                precio REAL NOT NULL,
                cantidad INTEGER NOT NULL
            )
        ''')
        conexion.commit() #Confirmamos la creación
        conexion.close() #Cerramos el puente

    def agregar_producto(self, producto): #Inserta un objeto Producto en la tabla SQL.
        conexion = self.conectar()
        cursor = conexion.cursor()
        try:
            cursor.execute('''
                INSERT INTO productos (id, nombre, categoria, precio, cantidad)
                VALUES (?,?,?,?,?)
            ''', (producto.id, producto.nombre, producto.categoria, producto.precio, producto.cantidad))
            conexion.commit() 
            print(f"Producto {producto.nombre} agregado con éxito.")
        except sqlite3.IntegrityError:
            print(f"Error: El ID {producto.id} ya existe en el sistema.")
        finally:
            conexion.close()

    def agregar_stock(self, id_prod, cantidad):
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()

            sql = '''
            UPDATE productos
            SET cantidad = cantidad + ?
            WHERE id = ?
            '''
            cursor.execute(sql, (cantidad, id_prod))
            conexion.commit()
            if cursor.rowcount > 0:
                print("El stock se añadió exitosamente.")
            else:
                print(f"ERROR: El ID {id_prod} no existe en el sistema.")
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
        finally: 
            conexion.close()
    

    # Búsqueda instantánea O(1) y control de stock mínimo
    def quitar_stock(self, id_prod, cantidad):
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()

            sql = '''
            UPDATE productos
            SET cantidad = cantidad - ?
            WHERE id = ? AND 
            cantidad >= ?
            '''
            cursor.execute(sql, (cantidad, id_prod, cantidad))
            conexion.commit()
            if cursor.rowcount > 0:
                print("El stock se restó exitosamente")
            else:
                print(f"ERROR: El ID {id_prod} no existe en el sistema o hay menos de {cantidad} unidades.")
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
        finally: 
            conexion.close()

    def eliminar_producto(self, id_prod):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()

            cursor.execute('''
            DELETE FROM productos
            WHERE id = ?     
        ''', (id_prod,))
            conexion.commit()
            if cursor.rowcount > 0:
                print("El producto se eliminó exitosamente.")
            else:
                print(f"ERROR: El ID {id_prod} no existe en el sistema.")
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
        finally: 
            conexion.close()

    def actualizar_precio_producto(self, id_prod, nuevo_precio):
        if nuevo_precio < 0:
            print("Error: El precio no puede ser negativo.")
            return

        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            
            # Solo actualizamos el precio para ese ID específico
            cursor.execute('''
                UPDATE productos 
                SET precio = ? 
                WHERE id = ?
            ''', (nuevo_precio, id_prod))
            
            conexion.commit()
            
            if cursor.rowcount > 0:
                print(f"Éxito: El precio del producto {id_prod} se actualizó a ${nuevo_precio:.2f}.")
            else:
                print(f"ERROR: El ID {id_prod} no existe en el sistema.")
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
        finally:
            conexion.close()

    def buscar_producto_por_id(self, id_prod):
        conexion = self.conectar()
        cursor = conexion.cursor()
        #Le pedimos a SQL que busque la fila
        cursor.execute("SELECT * FROM productos WHERE id = ?", (id_prod,))
        #Obtenemos el resultado (será una tupla o None)
        fila = cursor.fetchone()
        # Ya no necesitamos la conexión
        conexion.close() 
        if fila:
            # Convertimos la tupla (id, nombre, cat, precio, cant) de nuevo a un objeto Producto
            # fila[0] es ID, fila[1] es nombre, etc.
            return Producto(fila[0],fila[1],fila[2],fila[3],fila[4])
        else:
            return None

    def buscar_producto_por_nombre(self, nombre_parcial):
        conexion = self.conectar()
        cursor = conexion.cursor()
        # El % permite que busque coincidencias al inicio, medio o fin
        query = "SELECT * FROM productos WHERE nombre LIKE ?"
        cursor.execute(query, (f"%{nombre_parcial.lower()}%",))
        filas = cursor.fetchall()
        conexion.close()

        if filas:
            print(f"\nResultados para '{nombre_parcial}':")
            for f in filas:
                print(f"ID: {f[0]} | Nombre: {f[1].upper()} | Categoria: {f[2]} | Precio: {f[3]} | Stock: {f[4]}")
        else:
            print(f"No se encontraron productos que coincidan con '{nombre_parcial}'.")

    def reporte_stock_bajo(self, limite=5):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM productos WHERE cantidad <= ?", (limite,))
        filas = cursor.fetchall()
        conexion.close()

        if filas:
            print(f"\n⚠️ ALERTA DE STOCK BAJO (Menos de {limite} unidades) ⚠️")
            for f in filas:
                print(f"ID: {f[0]} | Producto: {f[1].upper()} | Cantidad: {f[4]}")
        else:
            print(f"\n✅ Todo bien: No hay productos con stock menor a {limite}.")

    def actualizar_precios_categoria(self, categoria, porcentaje):
        """
        porcentaje: ej. 10 para aumentar 10%, -5 para descontar 5%
        """
        factor = 1 + (porcentaje / 100)
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE productos 
                SET precio = precio * ? 
                WHERE categoria = ?
            ''', (factor, categoria.lower()))
            conexion.commit()
            
            if cursor.rowcount > 0:
                print(f"Éxito: Se actualizó el precio de {cursor.rowcount} productos de la categoría '{categoria}'.")
            else:
                print(f"No se encontraron productos en la categoría '{categoria}'.")
        except sqlite3.Error as e:
            print(f"Error: {e}")
        finally:
            conexion.close()

    def calcular_total(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        # hace la multiplicación y la suma en una sola pasada
        cursor.execute("SELECT SUM(precio * cantidad) FROM productos")
        
        # fetchone() devuelve una tupla, el resultado es el primer elemento [0]
        resultado = cursor.fetchone()[0]
        
        conexion.close()

        # Si la tabla está vacía, SUM devuelve None, por eso usamos 'or 0.0'
        total = resultado or 0.0
        print(f"VALOR TOTAL DEL INVENTARIO: ${total:,.2f}")
        return total

    def mostrar_inventario(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        # Pedimos todos los productos ordenados por nombre
        cursor.execute("SELECT * FROM productos ORDER BY nombre ASC")
        filas = cursor.fetchall() # Trae todas las filas de la tabla
        conexion.close()

        if not filas:
            print("El inventario está vacío.")
            return

        print("\n" + "="*70)
        print(f"{'ID':<10} {'NOMBRE':<20} {'CATEGORÍA':<15} {'PRECIO':<10} {'STOCK':<5}")
        print("-" * 70)

        for f in filas:
            # f[0]=id, f[1]=nombre, f[2]=cat, f[3]=precio, f[4]=cant
            p = Producto(f[0], f[1], f[2], f[3], f[4])
            
            print(f"{p.id:<10} {p.nombre.upper():<20} {p.categoria.upper():<15} {p.precio:<10.2f} {p.cantidad:<5}")
        print("-" * 75)
        self.calcular_total() 
        print("="*75 + "\n")

def solicitar_datos_producto(inventario):
    while True:
        id_prod = input("Ingrese el ID del producto: ").strip()
        if not id_prod:
            print("El ID no puede estar vacío.")
            continue
        
        # CAMBIO CLAVE: Usamos el método de la clase Inventario que consulta SQL
        if inventario.buscar_producto_por_id(id_prod) is not None:
            print(f"El ID {id_prod} ya existe en la base de datos. Inténtelo de nuevo.")
            continue 
        break 

    nombre = input("Ingrese el nombre del producto: ").strip()
    categoria = input("Ingrese la categoría del producto: ").strip()

    while True:
        try:
            precio = float(input("Ingrese el precio del producto: "))
            if precio < 0:
                print("El precio no puede ser negativo.")
                continue
            break 
        except ValueError:
            print("Error: Debe ingresar un número válido para el precio.")

    while True:
        try:
            cantidad = int(input("Ingrese la cantidad inicial: "))
            if cantidad < 0:
                print("La cantidad no puede ser negativa.")
                continue
            break 
        except ValueError:
            print("Error: Debe ingresar un número entero para la cantidad.")

    # Retornamos un OBJETO Producto para que sea fácil de insertar en SQL luego
    return Producto(id_prod, nombre, categoria, precio, cantidad)

def menu():
    mi_inventario = Inventario()
    while True:
        print("\n--- SISTEMA DE INVENTARIO ---")
        print("1. Agregar Producto")
        print("2. Eliminar Producto")
        print("3. Buscar Producto")
        print("4. Modificar precio producto/s")
        print("5. Mostrar inventario completo")
        print("6. Mostrar Productos por stock")
        print("7. Salir \n")
        
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            print("\n--- SISTEMA DE INVENTARIO ---")
            print("1.1 Crear Producto Nuevo")
            print("1.2 Añadir Stock existente")
            opcion = input("Seleccione una opción: ")
            if opcion == "1.1":
                nuevo = solicitar_datos_producto(mi_inventario)
                mi_inventario.agregar_producto(nuevo)
            elif opcion == "1.2":
                id_prod = input("Ingrese el ID del producto: ")   
                try:
                    cantidad = int(input("Ingrese la cantidad de unidades a añadir: "))
                    mi_inventario.agregar_stock(id_prod, cantidad) # El mensaje de éxito/error viene de la clase
                except ValueError:
                    print("Error: Debe ingresar un número entero.")      
            else:
                print("Opción no válida.")

        elif opcion == "2":
            print("\n--- SISTEMA DE INVENTARIO ---")
            print("2.1 Eliminar Producto")
            print("2.2 Quitar Stock existente")
            opcion = input("Seleccione una opción: ")
            if opcion == "2.1":
                id_prod = input("Ingrese el ID del Producto que desea eliminar: ")
                mi_inventario.eliminar_producto(id_prod)
            elif opcion == "2.2":
                id_prod = input("Ingrese el ID del producto: ")
                try:
                    cantidad = int(input("Ingrese la cantidad de unidades a quitar: "))
                    mi_inventario.quitar_stock(id_prod, cantidad)
                    print("Stock quitado exitosamente.")
                except ValueError as e:
                    print(f"{e}")
            else:
                print("Opción no válida.")

        elif opcion == "3":
            print("\n--- SISTEMA DE INVENTARIO ---")
            print("3.1 Buscar por ID")
            print("3.2 Buscar por nombre (multiresultado)")
            opcion = input("Seleccione una opción: ")
            if opcion == "3.1":
                dato = input("Ingrese el ID del Producto que desea buscar: ")
                resultado = mi_inventario.buscar_producto_por_id(dato)
                if resultado is not None:
                    print(f"Producto encontrado. \n ID: {resultado.id} | Nombre: {resultado.nombre.upper()} | Categoria: {resultado.categoria.upper()} | Precio: ${resultado.precio:.2f}")
                else:
                    print(f"El ID {dato} no existe en el sistema.")
            elif opcion == "3.2":
                nom = input("Escriba el nombre o parte del nombre a buscar: ")
                mi_inventario.buscar_producto_por_nombre(nom)
            else:
                print("Opción no válida.")

        elif opcion == "4":
            print("\n--- SISTEMA DE INVENTARIO ---")
            print("4.1 Modificar precio de un producto")
            print("4.2 Modificar precios de una categoria completa")
            opcion = input("Seleccione una opción: ")
            if opcion == "4.1":
                id_p = input("Ingrese el ID del producto a modificar: ")
                resultado = mi_inventario.buscar_producto_por_id(id_p)
                if resultado != None:
                    print(f"El precio actual del {resultado.nombre.upper()} es de ${resultado.precio}")
                    try:
                        n_precio = float(input("Ingrese el nuevo precio: "))
                        mi_inventario.actualizar_precio_producto(id_p, n_precio)
                    except ValueError:
                        print("Error: Ingrese un número válido para el precio.")
                else:
                    print(f"El ID {id_p} no existe en el sistema.")
            elif opcion == "4.2":
                cat = input("Categoría a actualizar: ")
                try:
                    por = float(input("Porcentaje de cambio (ej. 10 para aumento, -10 para rebaja): "))
                    mi_inventario.actualizar_precios_categoria(cat, por)
                except ValueError:
                    print("Error: El porcentaje debe ser un número (ej: 10.5).")
            else:
                print("Opción no válida.")

        elif opcion == "5":
            mi_inventario.mostrar_inventario()

        elif opcion == "6":
            try:
                lim = int(input("Defina el límite de stock para el reporte (ej. 5): "))
                mi_inventario.reporte_stock_bajo(lim)
            except ValueError:
                print("Error: El límite debe ser un número entero.")

        elif opcion == "7":
            print("Saliendo del sistema...")
            break

        else:
            print("Opción no válida.")

if __name__ == "__main__":
    menu()