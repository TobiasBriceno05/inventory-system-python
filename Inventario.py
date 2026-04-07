import json

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
        self.archivo = "BaseDeDatos.json"
        self.productos = {}
        self.cargar()

    def cargar(self):
        try: 
            with open(self.archivo, "r") as file:
                datos = json.load(file)
                for key, prod in datos.items():
                    self.productos[key] = Producto(prod["id"], prod["nombre"], prod["categoria"], prod["precio"], prod["cantidad"])
        except (FileNotFoundError, json.JSONDecodeError):
            self.productos = {} #Inicializa el inventario vacío

    def agregar_producto(self, producto):
        if producto.id in self.productos:
            raise ValueError(f"Error Crítico: El ID {producto.id} ya existe en el sistema.")
        self.productos[producto.id] = producto
        self.guardar_inventario()

    def agregar_stock(self, id_prod, cantidad):
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        if id_prod in self.productos:
            self.productos[id_prod].cantidad += cantidad
            self.guardar_inventario()
        else:
            raise ValueError(f"Error Crítico: El producto {id_prod} no existe en el sistema.")

    # Búsqueda instantánea O(1) y control de stock mínimo
    def quitar_stock(self, id_prod, cantidad):
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        if id_prod in self.productos:
            if self.productos[id_prod].cantidad >= cantidad:
                self.productos[id_prod].cantidad -= cantidad
                self.guardar_inventario()
            else:
                raise ValueError(f"Stock insuficiente. Solo hay {self.productos[id_prod].cantidad} unidades disponibles.")
        else:
            raise ValueError(f"Error Crítico: El producto {id_prod} no existe en el sistema.")

    def eliminar_producto(self, id_prod):
        if id_prod in self.productos:
            del self.productos[id_prod]
            self.guardar_inventario()
        else:
            raise ValueError(f"Error Crítico: El producto {id_prod} no existe en el sistema.")


    def buscar_producto(self, id_prod):
        if id_prod in self.productos:
            return self.productos[id_prod]
        raise ValueError(f"Error Crítico: El producto {id_prod} no existe en el sistema.")

    def calcular_total(self):
        total = 0
        for prod in self.productos.values():
            total += prod.precio * prod.cantidad
        return total

    def guardar_inventario(self):
        datos_para_json = {}
        for id_prod, contenido_p in self.productos.items():
            datos_para_json[id_prod] = contenido_p.to_dict() # Convierte el objeto Producto a un diccionario

        with open(self.archivo, "w") as file:
            json.dump(datos_para_json, file, indent=4)
    def mostrar_inventario(self):
        print(f"\n{'-'*75}")
        print(f"{'ID':<15} | {'NOMBRE':<15} | {'CATEGORÍA':<15} | {'PRECIO':<10} | {'CANTIDAD':<10}")
        print(f"{'-'*75}")
        for p in self.productos.values():
            print(f"{p.id:<15} | {p.nombre.upper():<15} | {p.categoria.upper():<15} | ${p.precio:<9.2f} | {p.cantidad:<10}")

def solicitar_datos_producto(inventario):
    while True:
        id_prod = input("Ingrese el ID del producto: ").strip()
        if not id_prod:
            print("El ID no puede estar vacío.")
            continue
        if id_prod in inventario.productos:
            print(f"El ID {id_prod} ya existe. Inténtelo de nuevo")
            continue #Reinicia el bucle
        break #El ID es válido y único
    nombre = input("Ingrese el nombre del producto: ").strip()
    categoria = input("Ingrese la categoria del producto: ").strip()
    while True:
        try:
            precio = float(input("Ingrese el precio del producto: "))
            if precio < 0:
                print("El precio no puede ser negativo. Inténtelo de nuevo.")
                continue #Termina esta iteración, vuelve a pedir el precio
            break #Caso contrario, el precio es válido
        except ValueError:
            print("Error: Debe ingresar un número.")
    while True:
        try:
            cantidad = int(input("Ingrese la cantidad del producto: "))
            if cantidad < 0:
                print("La cantidad no puede ser negativa. Inténtelo de nuevo.")
                continue #Termina esta iteración, vuelve a pedir la cantidad
            break #Caso contrario, la cantidad es válida
        except ValueError:
            print("Error: Debe ingresar un número.")
    return id_prod, nombre, categoria, precio, cantidad

def menu():
    mi_inventario = Inventario()
    while True:
        print("\n--- SISTEMA DE INVENTARIO ---")
        print("1. Agregar Producto")
        print("2. Eliminar Producto")
        print("3. Buscar Producto")
        print("4. Mostrar inventario completo")
        print("5. Salir \n")
        
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            print("\n--- SISTEMA DE INVENTARIO ---")
            print("1.1 Crear Producto Nuevo")
            print("1.2 Añadir Stock existente")
            opcion = input("Seleccione una opción: ")
            if opcion == "1.1":
                id, nombre, categoria, precio, cantidad = solicitar_datos_producto(mi_inventario)
                nuevo = Producto(id, nombre, categoria, precio, cantidad)
                mi_inventario.agregar_producto(nuevo)
                print("Producto agregado exitosamente.")
            elif opcion == "1.2":
                id_prod = input("Ingrese el ID del producto: ")
                try: 
                    cantidad = int(input("Ingrese la cantidad de unidades a añadir: "))
                    mi_inventario.agregar_stock(id_prod, cantidad)
                    print("Stock añadido exitosamente.")
                except ValueError as e:
                    print(f"{e}")
            else:
                print("Opción no válida.")
        elif opcion == "2":
            print("\n--- SISTEMA DE INVENTARIO ---")
            print("2.1 Eliminar Producto")
            print("2.2 Quitar Stock existente")
            opcion = input("Seleccione una opción: ")
            if opcion == "2.1":
                id_prod = input("Ingrese el ID del Producto que desea eliminar: ")
                try:
                    mi_inventario.eliminar_producto(id_prod)
                    print("Producto eliminado exitosamente.")
                except ValueError as e:
                    print(f"{e}")

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
            dato = input("Ingrese el ID del Producto que desea buscar: ")
            try:
                resultado = mi_inventario.buscar_producto(dato)
                print(f"Producto encontrado. \n ID: {resultado.id} | Nombre: {resultado.nombre.upper()} | Categoria: {resultado.categoria.upper()} | Precio: ${resultado.precio:.2f}")
            except ValueError as e:
                print(f"{e}")
        elif opcion == "4":
            mi_inventario.mostrar_inventario()
            print(f"\n \n Valor Total del inventario: ${mi_inventario.calcular_total():.2f}")
        elif opcion == "5":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    menu()