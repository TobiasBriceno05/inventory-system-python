import json

class Producto:
    def __init__(self, id, nombre, categoria, precio):
        self.id = id
        self.nombre = nombre.lower()
        self.categoria = categoria.lower()
        self.precio = float(precio)
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
        self.productos[producto.id] = producto
        self.guardar()

    def eliminar(self, id):
        if id in self.productos:
            del self.productos[id]
            self.guardar()

    def buscar(self, nombre):
        for prod in self.productos.values():
            if prod.nombre == nombre.lower():
                return prod.id
        return None

    def guardar(self):
        datos_para_json = {}
        for id_p, contenido_p in self.productos.items():
            diccionario_simple = contenido_p.to_dict()
            datos_para_json[id_p] = diccionario_simple

        with open(self.archivo, "w") as file:
            json.dump(datos_para_json, file, indent=4)

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
            datos = input("Ingrese ID, Nombre, Categoría y Precio del Producto (separado por espacio): ").split()
            if len(datos) == 4:
                nuevo = Producto(datos[0],datos[1],datos[2],datos[3])
                mi_inventario.agregar(nuevo)
                print("Producto agregado exitosamente.")
            else:
                print ("Error, Intentelo de nuevo.")
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
                print(f"Producto encontrado. ID: {resultado}.")
            else:
                print("Producto no encontrado.")
        elif opcion == "4":
            print("\nID         | NOMBRE     | CATEGORÍA  | PRECIO")
            print("-" * 45)
            for p in mi_inventario.productos.values():
                print(f"{p.id:10} | {p.nombre:10} | {p.categoria:10} | ${p.precio:.2f}")
        elif opcion == "5":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción no válida.")
menu()