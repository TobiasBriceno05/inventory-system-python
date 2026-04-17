import sqlite3
import shutil
import os
import hashlib
from datetime import datetime
import pytz

class Producto:
    def __init__(self, id_prod, nombre, categoria, precio, costo=0.0, cantidad=0):
        if precio < 0:
            raise ValueError("El precio no puede ser negativo") # Fail-fast
        if costo < 0:
            raise ValueError("El costo no puede ser negativo")
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa")
        self.id = id_prod
        self.nombre = nombre.upper()
        self.categoria = categoria.upper()
        self.precio = precio
        self.costo = costo
        self.cantidad = cantidad # Si no se proporciona una cantidad, se establece en 0
    def to_dict(self):
        return {"id" : self.id, "nombre" : self.nombre, "categoria" : self.categoria, "precio" : self.precio, "costo": self.costo, "cantidad" : self.cantidad}

class Inventario:
    def __init__(self):
        self.archivo_db = "BaseDeDatos.db"
        self.crear_tabla()
        self.aplicar_migraciones()

    def aplicar_migraciones(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        migraciones = [
            "ALTER TABLE productos ADD COLUMN costo REAL DEFAULT 0.0",
            "ALTER TABLE ventas ADD COLUMN subtotal REAL DEFAULT 0.0",
            "ALTER TABLE ventas ADD COLUMN iva REAL DEFAULT 0.0",
            "ALTER TABLE detalle_ventas ADD COLUMN costo_unitario REAL DEFAULT 0.0",
            "ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'"
        ]
        for query in migraciones:
            try:
                cursor.execute(query)
            except sqlite3.OperationalError:
                pass # La columna ya existe
        # Insertar IVA por defecto si no existe
        try:
            cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('IVA', '16')")
        except sqlite3.OperationalError:
            pass
        conexion.commit()
        conexion.close()

    def conectar(self):
        # Es vital usar check_same_thread=False para cuando usemos la GUI
        return sqlite3.connect(self.archivo_db, check_same_thread=False)

    def crear_tabla(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        # Obligamos a SQLite a respetar las relaciones entre tablas
        cursor.execute("PRAGMA foreign_keys = ON")

        # 0. Configuración
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        ''')

        # 1. Productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,

                categoria TEXT NOT NULL,
                precio REAL NOT NULL,
                costo REAL DEFAULT 0.0,
                cantidad INTEGER NOT NULL
            )
        ''')

        # 2. Clientes (Para ropa/electrónica)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id_cliente TEXT PRIMARY KEY, -- Cédula o RIF
                nombre TEXT NOT NULL,
                telefono TEXT,
                email TEXT
            )
        ''')

        # 3. Ventas (La factura global)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                id_cliente TEXT,
                subtotal REAL DEFAULT 0.0,
                iva REAL DEFAULT 0.0,
                total REAL NOT NULL,
                FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
            )
        ''')

        # 4. Detalle de Ventas (Los renglones de la factura)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                id_venta INTEGER,
                id_producto TEXT,
                cantidad INTEGER,
                precio_unitario REAL,
                costo_unitario REAL DEFAULT 0.0,
                FOREIGN KEY (id_venta) REFERENCES ventas (id),
                FOREIGN KEY (id_producto) REFERENCES productos (id)
            )
        ''')
        
        # 5. Devoluciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devoluciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                id_venta INTEGER,
                total_devuelto REAL,
                FOREIGN KEY (id_venta) REFERENCES ventas (id)
            )
        ''')

        # 6. Detalle de Devoluciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_devoluciones (
                id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                id_devolucion INTEGER,
                id_producto TEXT,
                cantidad INTEGER,
                precio_unitario REAL,
                costo_unitario REAL,
                FOREIGN KEY (id_devolucion) REFERENCES devoluciones (id),
                FOREIGN KEY (id_producto) REFERENCES productos (id)
            )
        ''')

        # 7. Usuarios para Login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Insertar administrador por defecto ("admin" / "admin123") si no hay usuarios
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            pass_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
            cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", ("admin", pass_hash))

        conexion.commit()
        conexion.close()
    
    def verificar_login(self, usuario, password):
        conexion = self.conectar()
        cursor = conexion.cursor()
        pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        cursor.execute("SELECT id, usuario FROM usuarios WHERE usuario = ? AND password = ?", (usuario, pass_hash))
        resultado = cursor.fetchone()
        conexion.close()
        
        return resultado

    
    def obtener_iva(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave='IVA'")
        resultado = cursor.fetchone()
        conexion.close()
        try:
            return float(resultado[0]) if resultado else 16.0
        except ValueError:
            return 16.0

    def actualizar_iva(self, nuevo_iva):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("UPDATE configuracion SET valor=? WHERE clave='IVA'", (str(nuevo_iva),))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('IVA', ?)", (str(nuevo_iva),))
        conexion.commit()
        conexion.close()
        return True
    def registrar_cliente(self, id_cliente, nombre, telefono, email):
        """
        Registra un nuevo cliente en la base de datos.
        id_cliente actúa como la llave primaria (Cédula/RIF).
        """
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            
            query = '''
                INSERT INTO clientes (id_cliente, nombre, telefono, email)
                VALUES (?, ?, ?, ?)
            '''
            cursor.execute(query, (id_cliente, nombre, telefono, email))
            
            conexion.commit()
            print(f"✅ Cliente '{nombre}' registrado con éxito.")
            return True
            
        except sqlite3.IntegrityError:
            print(f"❌ Error: Ya existe un cliente registrado con el ID {id_cliente}.")
            return False
        except Exception as e:
            print(f"⚠️ Error inesperado: {e}")
            return False
        finally:
            conexion.close()

    def buscar_cliente(self, id_cliente):
        """Busca un cliente por su ID y retorna sus datos."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,))
        cliente = cursor.fetchone()
        
        conexion.close()
        return cliente # Retorna una tupla (id, nombre, tel, email) o None

    def listar_clientes(self):
        """Retorna todos los clientes registrados en la base de datos."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        conexion.close()
        return clientes

    def eliminar_cliente(self, id_cliente):
        """Elimina un cliente verificando que no tenga ventas asociadas."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            
            # Verificar integridad referencial (ventas asociadas)
            cursor.execute("SELECT id FROM ventas WHERE id_cliente = ?", (id_cliente,))
            ventas = cursor.fetchall()
            if ventas:
                raise ValueError("No se puede eliminar el cliente porque tiene ventas asociadas.")
                
            cursor.execute("DELETE FROM clientes WHERE id_cliente = ?", (id_cliente,))
            conexion.commit()
            if cursor.rowcount > 0:
                print(f"✅ Cliente {id_cliente} eliminado con éxito.")
                return True
            else:
                print(f"❌ Error: El cliente {id_cliente} no existe.")
                return False
        except ValueError as ve:
            print(ve)
            raise ve # Relanzar para manejar el messagebox en la GUI
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
            return False
        finally:
            conexion.close()

    def actualizar_cliente(self, id_cliente, telefono, email):
        """Actualiza el teléfono y correo (dirección) de un cliente."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("UPDATE clientes SET telefono=?, email=? WHERE id_cliente=?", (telefono, email, id_cliente))
            conexion.commit()
            if cursor.rowcount > 0:
                print(f"✅ Cliente {id_cliente} actualizado con éxito.")
                return True
            else:
                return False
        except sqlite3.Error as e:
            print(f"Error actualizando cliente: {e}")
            return False
        finally:
            conexion.close()

    def registrar_venta(self, id_cliente, lista_productos, metodo_pago="Efectivo"):
        """
        Registra una venta completa.
        lista_productos debe ser una lista de tuplas: [(id_producto, cantidad), ...]
        """
        conexion = self.conectar()
        try:
            conexion.execute("PRAGMA foreign_keys = ON")
            cursor = conexion.cursor()
            
            # INICIO DE LA TRANSACCIÓN
            cursor.execute("BEGIN TRANSACTION")

            # 1. Verificar si el cliente existe (Regla estricta)
            cursor.execute("SELECT nombre FROM clientes WHERE id_cliente = ?", (id_cliente,))
            if not cursor.fetchone():
                raise ValueError(f"El cliente con ID {id_cliente} no existe.")

            subtotal_venta = 0
            detalles = []

            # 2. Validar stock y calcular precios
            for id_prod, cant_vender in lista_productos:
                cursor.execute("SELECT nombre, precio, costo, cantidad FROM productos WHERE id = ?", (id_prod,))
                producto = cursor.fetchone()

                if not producto:
                    raise ValueError(f"El producto {id_prod} no existe.")
                
                nombre_p, precio_p, costo_p, stock_p = producto

                if stock_p < cant_vender:
                    raise ValueError(f"Stock insuficiente para {nombre_p}. Disponible: {stock_p}")

                subtotal = precio_p * cant_vender
                subtotal_venta += subtotal
                
                # Guardamos los datos para el detalle
                detalles.append((id_prod, cant_vender, precio_p, costo_p))

                # 3. Restar stock del producto
                cursor.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?", (cant_vender, id_prod))

            # Obtener IVA configurado y calcular a la inversa (IVA Incluido)
            porcentaje_iva = self.obtener_iva()
            total_venta = subtotal_venta # Ya que el precio de los productos incluye el IVA
            base_imponible = total_venta / (1 + (porcentaje_iva / 100.0))
            monto_iva = total_venta - base_imponible

            tz_vzla = pytz.timezone('America/Caracas')
            fecha_hoy = datetime.now(tz_vzla).strftime('%Y-%m-%d %H:%M:%S')

            # 4. Crear el encabezado de la venta (guardamos base imponible en la columna subtotal)
            cursor.execute("INSERT INTO ventas (fecha, id_cliente, subtotal, iva, total, metodo_pago) VALUES (?, ?, ?, ?, ?, ?)", (fecha_hoy, id_cliente, base_imponible, monto_iva, total_venta, metodo_pago))
            id_factura = cursor.lastrowid # Obtenemos el ID generado automáticamente

            # 5. Crear los detalles de la venta
            for id_p, cant, precio, costo in detalles:
                cursor.execute('''
                    INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, costo_unitario)
                    VALUES (?, ?, ?, ?, ?)
                ''', (id_factura, id_p, cant, precio, costo))

            # SI TODO SALIÓ BIEN, GUARDAMOS
            conexion.commit()
            print(f"✅ Venta #{id_factura} registrada con éxito por un total de ${total_venta:.2f}")
            # Retornar más información de la venta para el ticket
            return {
                "exito": True,
                "id_venta": id_factura,
                "fecha": fecha_hoy,
                "subtotal": subtotal_venta,
                "iva": monto_iva,
                "total": total_venta,
                "productos": lista_productos
            }

        except Exception as e:
            # SI ALGO FALLA, DESHACEMOS TODO
            conexion.rollback()
            print(f"❌ Error en la venta: {e}")
            return {"exito": False, "error": str(e)}
        finally:
            conexion.close()

    def agregar_producto(self, producto): #Inserta un objeto Producto en la tabla SQL.
        conexion = self.conectar()
        cursor = conexion.cursor()
        try:
            # Asegúrate de activar esto si no lo hiciste en el __init__
            cursor.execute("PRAGMA foreign_keys = ON") 
            
            cursor.execute('''
                INSERT INTO productos (id, nombre, categoria, precio, costo, cantidad)
                VALUES (?,?,?,?,?,?)
            ''', (producto.id, producto.nombre, producto.categoria, producto.precio, producto.costo, producto.cantidad))
            conexion.commit() 
            print(f"Producto {producto.nombre} agregado con éxito.")
            return True # Éxito
        except sqlite3.IntegrityError:
            print(f"Error: El ID {producto.id} ya existe en el sistema.")
            return False # Falló por duplicado
        finally:
            conexion.close()

    def listar_productos(self):
        """Retorna todos los productos para llenar la tabla de la GUI."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, categoria, precio, costo, cantidad FROM productos")
        productos = cursor.fetchall()
        conexion.close()
        return [(p[0], p[1].upper(), p[2].upper(), p[3], p[4], p[5]) for p in productos]

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

    def buscar_productos_filtro(self, criterio):
        """
        Busca productos que coincidan con el criterio en ID o Nombre.
        Retorna una lista de tuplas.
        """
        conexion = self.conectar()
        cursor = conexion.cursor()
        # Buscamos coincidencias en ID o Nombre usando el operador LIKE (case-insensitive en SQLite por defecto para ASCII)
        criterio_upper = f"%{criterio.upper()}%"
        query = "SELECT * FROM productos WHERE UPPER(id) LIKE ? OR UPPER(nombre) LIKE ?"
        cursor.execute(query, (criterio_upper, criterio_upper))
        resultados = cursor.fetchall()
        conexion.close()
        return resultados

    def reporte_stock_bajo(self, limite=5):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM productos WHERE cantidad <= ?", (limite,))
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def procesar_devolucion(self, id_venta, lista_productos_devueltos):
        """
        Genera una nota de crédito/devolución.
        lista_productos_devueltos: [(id_producto, cantidad), ...]
        """
        conexion = self.conectar()
        try:
            conexion.execute("PRAGMA foreign_keys = ON")
            cursor = conexion.cursor()
            cursor.execute("BEGIN TRANSACTION")

            # Verificar si la venta existe
            cursor.execute("SELECT id, iva, subtotal, total FROM ventas WHERE id = ?", (id_venta,))
            venta = cursor.fetchone()
            if not venta:
                raise ValueError(f"La venta #{id_venta} no existe.")

            total_devuelto = 0
            detalles_a_devolver = []

            for id_prod, cant_devolver in lista_productos_devueltos:
                # Verificamos detalle_ventas para asegurar que ese producto se vendió en esa venta a ese precio
                cursor.execute("SELECT cantidad, precio_unitario, costo_unitario FROM detalle_ventas WHERE id_venta = ? AND id_producto = ?", (id_venta, id_prod))
                detalle = cursor.fetchone()
                if not detalle:
                    raise ValueError(f"El producto {id_prod} no fue parte de la venta #{id_venta}.")
                
                cant_vendida, p_unit, c_unit = detalle

                # Verificar historial de devoluciones anteriores
                cursor.execute("""
                    SELECT SUM(dd.cantidad)
                    FROM detalle_devoluciones dd
                    JOIN devoluciones d ON dd.id_devolucion = d.id
                    WHERE d.id_venta = ? AND dd.id_producto = ?
                """, (id_venta, id_prod))
                devueltas_previas = cursor.fetchone()[0] or 0
                max_retornable = cant_vendida - devueltas_previas

                if cant_devolver > max_retornable:
                    raise ValueError(f"Intentas devolver {cant_devolver}x {id_prod}, pero solo restan {max_retornable} disponibles en esta factura.")

                subtotal_prod = p_unit * cant_devolver
                total_devuelto += subtotal_prod

                detalles_a_devolver.append((id_prod, cant_devolver, p_unit, c_unit))

                # Retornamos el stock al inventario
                cursor.execute("UPDATE productos SET cantidad = cantidad + ? WHERE id = ?", (cant_devolver, id_prod))

            # Calcular IVA correspondiente a la porción devuelta, suponiendo que el IVA aplicado es el global u obtenido
            # Si guardamos el IVA y Subtotal en base de datos de la venta original:
            _, iva_venta, subtotal_venta, _ = venta
            if subtotal_venta > 0:
                proporcion = total_devuelto / subtotal_venta
                iva_devuelto = iva_venta * proporcion
            else:
                iva_devuelto = 0
            total_factura_devuelto = total_devuelto

            tz_vzla = pytz.timezone('America/Caracas')
            fecha_hoy = datetime.now(tz_vzla).strftime('%Y-%m-%d %H:%M:%S')

            # Registrar en tabla devoluciones
            cursor.execute("INSERT INTO devoluciones (fecha, id_venta, total_devuelto) VALUES (?, ?, ?)", (fecha_hoy, id_venta, total_factura_devuelto))
            id_devolucion = cursor.lastrowid

            for id_p, cant, p_unit, c_unit in detalles_a_devolver:
                cursor.execute('''
                    INSERT INTO detalle_devoluciones (id_devolucion, id_producto, cantidad, precio_unitario, costo_unitario)
                    VALUES (?, ?, ?, ?, ?)
                ''', (id_devolucion, id_p, cant, p_unit, c_unit))

            conexion.commit()
            return True, total_factura_devuelto
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    def obtener_reporte_cierre(self, fecha):
        """
        Retorna:
        - Total Ventas Brutas
        - Total IVA recaudado
        - Total Costo (COGS)
        - Total Devoluciones
        - Ganancia Neta
        """
        conexion = self.conectar()
        cursor = conexion.cursor()
        # Fecha suele venir tipo 'YYYY-MM-DD'
        fecha_like = f"{fecha}%"

        # Calcular Ventas Generales
        cursor.execute("SELECT SUM(subtotal), SUM(iva), SUM(total) FROM ventas WHERE fecha LIKE ?", (fecha_like,))
        ventas_res = cursor.fetchone()
        sub_ventas = ventas_res[0] or 0.0
        iva_ventas = ventas_res[1] or 0.0

        # Calcular Costo de la Mercancía Vendida (COGS)
        cursor.execute('''
            SELECT SUM(dv.cantidad * dv.costo_unitario) 
            FROM detalle_ventas dv
            JOIN ventas v ON dv.id_venta = v.id
            WHERE v.fecha LIKE ?
        ''', (fecha_like,))
        cogs_res = cursor.fetchone()
        costo_ventas = cogs_res[0] or 0.0

        # Calcular Devoluciones
        cursor.execute("SELECT SUM(total_devuelto) FROM devoluciones WHERE fecha LIKE ?", (fecha_like,))
        dev_res = cursor.fetchone()
        total_dev = dev_res[0] or 0.0

        # Calcular Costo de la Mercancía Devuelta (vuelve al inventario, por lo que resta al COGS)
        cursor.execute('''
            SELECT SUM(dd.cantidad * dd.costo_unitario)
            FROM detalle_devoluciones dd
            JOIN devoluciones d ON dd.id_devolucion = d.id
            WHERE d.fecha LIKE ?
        ''', (fecha_like,))
        cogs_dev_res = cursor.fetchone()
        costo_devuelto = cogs_dev_res[0] or 0.0

        # Calcular ventas por método de pago y agrupar en divisas / bolívares
        cursor.execute('''
            SELECT UPPER(metodo_pago), SUM(total) 
            FROM ventas 
            WHERE fecha LIKE ? 
            GROUP BY UPPER(metodo_pago)
        ''', (fecha_like,))
        totales_crudos = dict(cursor.fetchall())

        divisas_usd = totales_crudos.get('EFECTIVO', 0.0) + totales_crudos.get('ZELLE', 0.0)
        bolivares_ves = totales_crudos.get('PAGO MÓVIL', 0.0) + totales_crudos.get('TARJETA / POS', 0.0)

        totales_por_metodo = {
            "Divisas (USD)": divisas_usd,
            "Bolívares (VES)": bolivares_ves
        }

        # Calcular Devoluciones originadas en Efectivo
        cursor.execute('''
            SELECT SUM(d.total_devuelto) 
            FROM devoluciones d 
            JOIN ventas v ON d.id_venta = v.id 
            WHERE d.fecha LIKE ? AND UPPER(v.metodo_pago) = 'EFECTIVO'
        ''', (fecha_like,))
        dev_efectivo_res = cursor.fetchone()
        total_dev_efectivo = dev_efectivo_res[0] or 0.0

        # Traer todas las ventas del día ordenadas
        cursor.execute('''
            SELECT id, fecha, id_cliente, total, metodo_pago
            FROM ventas
            WHERE fecha LIKE ?
            ORDER BY fecha DESC
        ''', (fecha_like,))
        lista_ventas_dia = []
        for v in cursor.fetchall():
            lista_ventas_dia.append({
                "id_venta": v[0],
                "fecha": v[1],
                "id_cliente": v[2],
                "total": v[3],
                "metodo_pago": v[4] if v[4] else "Desconocido"
            })

        conexion.close()

        iva_porcentaje = self.obtener_iva()
        subtotal_dev = total_dev / (1 + (iva_porcentaje / 100))
        iva_dev = total_dev - subtotal_dev

        ingreso_bruto = sub_ventas - subtotal_dev
        cogs_final = costo_ventas - costo_devuelto
        ganancia_neta = ingreso_bruto - cogs_final

        efectivo_ventas = totales_crudos.get('EFECTIVO', 0.0)
        efectivo_real = efectivo_ventas - total_dev_efectivo

        return {
            "ingreso_bruto_sin_iva": ingreso_bruto,
            "iva_recaudado": iva_ventas - iva_dev,
            "cogs": cogs_final,
            "total_devoluciones": total_dev,
            "ganancia_neta_estimada": ganancia_neta,
            "efectivo_real_en_caja": efectivo_real,
            "totales_por_metodo": totales_por_metodo,
            "ventas_dia": lista_ventas_dia
        }

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
                WHERE UPPER(categoria) = UPPER(?)
            ''', (factor, categoria))
            conexion.commit()
            
            if cursor.rowcount > 0:
                print(f"Éxito: Se actualizó el precio de {cursor.rowcount} productos de la categoría '{categoria}'.")
                return True
            else:
                print(f"No se encontraron productos en la categoría '{categoria}'.")
                return False
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return False
        finally:
            conexion.close()

    def obtener_ventas_ultimos_7_dias(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT date(fecha) as dia, SUM(total)
            FROM ventas
            WHERE date(fecha) >= date('now', 'localtime', '-7 days')
            GROUP BY date(fecha)
            ORDER BY date(fecha) ASC
        ''')
        res = cursor.fetchall()
        conexion.close()
        return res

    def obtener_top_productos_30_dias(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT UPPER(p.nombre), SUM(dv.cantidad)
            FROM detalle_ventas dv
            JOIN productos p ON dv.id_producto = p.id
            JOIN ventas v ON dv.id_venta = v.id
            WHERE date(v.fecha) >= date('now', 'localtime', '-30 days')
            GROUP BY UPPER(p.nombre)
            ORDER BY SUM(dv.cantidad) DESC
            LIMIT 5
        ''')
        res = cursor.fetchall()
        conexion.close()
        return res

    def obtener_valor_total_almacen_costo(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT SUM(costo * cantidad) FROM productos WHERE cantidad > 0")
        res = cursor.fetchone()[0]
        conexion.close()
        return res or 0.0

    def obtener_productos_muertos_30_dias(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT id, UPPER(nombre), cantidad 
            FROM productos 
            WHERE id NOT IN (
                SELECT dv.id_producto 
                FROM detalle_ventas dv
                JOIN ventas v ON dv.id_venta = v.id
                WHERE date(v.fecha) >= date('now', 'localtime', '-30 days')
            )
            ORDER BY cantidad DESC
        ''')
        res = cursor.fetchall()
        conexion.close()
        return res

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
    
    def obtener_total_productos(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT SUM(cantidad) FROM productos")
        resultado = cursor.fetchone()[0]
        conexion.close()
        return resultado if resultado else 0

    def obtener_total_clientes(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM clientes")
        resultado = cursor.fetchone()[0]
        conexion.close()
        return resultado if resultado else 0
    
    def _agrupar_ventas(self, query, params=()):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conexion.close()

        ventas_agrupadas = {}
        for f in filas:
            id_v, fecha, id_c, nom_c, total, p_nom, p_cant, p_precio, metodo_pago = f
            if id_v not in ventas_agrupadas:
                ventas_agrupadas[id_v] = {
                    "id": id_v,
                    "fecha": fecha,
                    "id_cliente": id_c,
                    "nombre_cliente": nom_c if nom_c else "Desconocido",
                    "total": total,
                    "metodo_pago": metodo_pago if metodo_pago else "Desconocido",
                    "productos": []
                }
            ventas_agrupadas[id_v]["productos"].append({
                "nombre": p_nom,
                "cantidad": p_cant,
                "precio_unitario": p_precio,
                "subtotal": p_cant * p_precio
            })
            
        return sorted(list(ventas_agrupadas.values()), key=lambda x: x['fecha'], reverse=True)

    def obtener_todas_las_ventas(self):
        query = """
            SELECT v.id, v.fecha, v.id_cliente, c.nombre, v.total, p.nombre, dv.cantidad, dv.precio_unitario, v.metodo_pago
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
            JOIN detalle_ventas dv ON v.id = dv.id_venta
            JOIN productos p ON dv.id_producto = p.id
            ORDER BY v.fecha DESC
        """
        return self._agrupar_ventas(query)

    def obtener_historial_cliente(self, cedula):
        query = """
            SELECT v.id, v.fecha, v.id_cliente, c.nombre, v.total, p.nombre, dv.cantidad, dv.precio_unitario, v.metodo_pago
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
            JOIN detalle_ventas dv ON v.id = dv.id_venta
            JOIN productos p ON dv.id_producto = p.id
            WHERE v.id_cliente = ?
            ORDER BY v.fecha DESC
        """
        return self._agrupar_ventas(query, (cedula,))
        
    def respaldar_base_datos(self):
        try:
            os.makedirs("Backups", exist_ok=True)
            ahora = datetime.now()
            nombre_db = self.archivo_db
            nombre_backup = f"Backups/Backup_{ahora.strftime('%Y_%m_%d_%H%M')}.db"
            
            # Es importante asegurar que todas las transacciones estén cerradas,
            # pero desde Sqlite un copy via file system suele funcionar para snapshots rapidos locales.
            shutil.copy2(nombre_db, nombre_backup)
            print(f"Copia de seguridad local creada: {nombre_backup}")
            return True, nombre_backup
        except Exception as e:
            print(f"Error gestionando copia de seguridad: {e}")
            return False, str(e)
