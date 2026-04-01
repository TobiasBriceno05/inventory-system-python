import json

class Producto:
    def __init__(self, id_prod, nombre, categoria, precio):
        if precio < 0:
            raise ValueError("El precio no puede ser negativo") # Fail-fast
        self.id = id_prod
        self.nombre = nombre.lower()
        self.categoria = categoria.lower()
        self.precio = precio
    def to_dict(self):
        return {"id" : self.id, "nombre" : self.nombre, "categoria" : self.categoria, "precio" : self.precio}

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
                    self.productos[key] = Producto(prod["id"], prod["nombre"], prod["categoria"], prod["precio"])
        except FileNotFoundError:
            self.productos = {}

    def agregar(self, producto):
        if producto.id in self.productos:
            raise ValueError(f"Error Crítico: El ID {producto.id} ya existe en el sistema.")
        self.productos[producto.id] = producto
        self.guardar()

    def eliminar(self, id_prod):
        if id_prod in self.productos:
            del self.productos[id_prod]
            self.guardar()

    def buscar(self, nombre):
        for prod in self.productos.values():
            if prod.nombre == nombre.lower():
                return prod
        return None

    def guardar(self):
        datos_para_json = {}
        for id_prod, contenido_p in self.productos.items():
            diccionario_simple = contenido_p.to_dict()
            datos_para_json[id_prod] = diccionario_simple

        with open(self.archivo, "w") as file:
            json.dump(datos_para_json, file, indent=4)
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
    return id_prod, nombre, categoria, precio
def menu():
    mi_inventario = Inventario()
    while True:
        print("\n--- SISTEMA DE INVENTARIO ---")
        print("1. Agregar Producto")
        print("2. Eliminar Producto")
        print("3. Buscar por Nombre")
        print("4. Mostrar Todo")
        print("5. Salir \n")
        
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            id, nombre, categoria, precio = solicitar_datos_producto(mi_inventario)
            nuevo = Producto(id, nombre, categoria, precio)
            mi_inventario.agregar(nuevo)
            print("Producto agregado exitosamente.")
        elif opcion == "2":
            dato = input("Ingrese el ID del Producto que desea eliminar: ")
            if dato in mi_inventario.productos:
                mi_inventario.eliminar(dato)
                print("Producto eliminado exitosamente.")
            else:
                print("Producto no encontrado.")
        elif opcion == "3":
            dato = input("Ingrese el nombre del Producto que desea buscar: ")
            resultado = mi_inventario.buscar(dato)
            if resultado:
                print(f"Producto encontrado. \n ID: {resultado.id} | Nombre: {resultado.nombre.upper()} | Categoria: {resultado.categoria.upper()} | Precio: ${resultado.precio:.2f}")
            else:
                print("Producto no encontrado.")
        elif opcion == "4":
            print("\n      ID        |      NOMBRE     |    CATEGORÍA    |    PRECIO")
            print("-" * 45)
            for p in mi_inventario.productos.values():
                print(f"{p.id:15} | {p.nombre.upper():15} | {p.categoria.upper():15} | ${p.precio:.2f}")
        elif opcion == "5":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    menu()