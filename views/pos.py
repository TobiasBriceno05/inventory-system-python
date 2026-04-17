import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pytz
import os
import csv
from Inventario import Inventario, Producto
from generador_pdf import generar_pdf_factura, generar_pdf_cierre_caja
from style_config import StyleConfig

class POSView(ctk.CTkFrame):
    def _crear_dialogo(self, titulo, label_texto, callback, max_stock):
        ventana_dialog = ctk.CTkToplevel(self.app)
        ventana_dialog.title(titulo)
        ventana_dialog.geometry("400x250")
        ventana_dialog.configure(fg_color="#141416")
        ventana_dialog.attributes('-topmost', True)
        
        ctk.CTkLabel(ventana_dialog, text=titulo.upper(), font=ctk.CTkFont(family=StyleConfig.font_title[0], size=16, weight="bold"), text_color=StyleConfig.accent_primary).pack(pady=(20, 10))
        ctk.CTkLabel(ventana_dialog, text=label_texto, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_main).pack(pady=5)
        
        entrada = ctk.CTkEntry(
            ventana_dialog, 
            width=200, height=40,
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14),
            fg_color=StyleConfig.bg_base, border_color=StyleConfig.border_subtle, corner_radius=15
        )
        entrada.pack(pady=10)
        
        def procesar():
            val = entrada.get().strip()
            if not val:
                messagebox.showwarning("Vacío", "El campo no puede estar vacío.", parent=ventana_dialog)
                return
            try: 
                cant = int(val)
                if cant <= 0: return
                if cant > max_stock:
                    messagebox.showerror("Sin Stock", f"Stock físico excedido. Máximo permitido: {max_stock}.", parent=ventana_dialog)
                    return
                ventana_dialog.destroy()
                callback(cant)
            except ValueError: 
                messagebox.showerror("Error", "Debe ser número entero positivo", parent=ventana_dialog)
            
        btn = ctk.CTkButton(ventana_dialog, text="CONFIRMAR", command=procesar, fg_color=StyleConfig.accent_primary, text_color="#000", font=ctk.CTkFont(family=StyleConfig.font_button[0], weight="bold"), height=40, corner_radius=15, hover_color="#EAB308")
        btn.pack(pady=10)

    def agregar_al_carrito(self, event):
        seleccion = self.tabla_pos_busqueda.selection() 
        if not seleccion: return
            
        datos = self.tabla_pos_busqueda.item(seleccion)['values']
        id_p, nombre_p, _, precio_p_str, _, stock_p = datos 
        precio_p = float(str(precio_p_str).replace('$', '').replace(',', ''))

        if stock_p <= 0:
            messagebox.showwarning("Sin Stock", "ESTE ARTÍCULO ESTÁ AGOTADO.")
            return

        def on_confirm(can_agregar):
            encontrado = False
            for item in self.carrito:
                if item['id'] == id_p:
                    if (item['cantidad'] + can_agregar) <= stock_p: 
                        item['cantidad'] += can_agregar
                        encontrado = True
                    else:
                        messagebox.showwarning("Sin Stock", f"Stock físico excedido. Máximo permitido: {stock_p}.")
                        return
                    break
            
            if not encontrado:
                self.carrito.append({
                    "id": id_p,
                    "nombre": nombre_p,
                    "precio": precio_p,
                    "cantidad": can_agregar,
                    "stock_max": stock_p
                })
            self.actualizar_tabla_carrito_visual()

        self._crear_dialogo("Entrada de Venta", f"CANTIDAD A VENDER de {nombre_p} (Stock: {stock_p}):", on_confirm, stock_p)


    def eliminar_del_carrito(self):
        seleccion = self.tabla_pos_carrito.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una fila en el checklist industrial.")
            return
            
        id_a_borrar = self.tabla_pos_carrito.item(seleccion)['values'][0]
        id_real = str(id_a_borrar).replace("[", "").replace("]", "")
        self.carrito = [item for item in self.carrito if str(item['id']) != id_real]
        self.actualizar_tabla_carrito_visual()

    def vaciar_carrito(self):
        if not self.carrito: return
        if messagebox.askyesno("Confirmar Purga", "¿ELIMINAR todos los registros del flujo actual?"):
            self.carrito = []
            self.actualizar_tabla_carrito_visual()

    def restar_unidad_carrito(self):
        seleccion = self.tabla_pos_carrito.selection()
        if not seleccion: return
        id_sel = self.tabla_pos_carrito.item(seleccion)['values'][0]
        id_real = str(id_sel).replace("[", "").replace("]", "")
        
        for item in self.carrito:
            if str(item['id']) == id_real:
                if item['cantidad'] > 1:
                    item['cantidad'] -= 1
                    self.actualizar_tabla_carrito_visual()
                else:
                    self.eliminar_del_carrito()
                break

    def sumar_unidad_carrito(self):
        seleccion = self.tabla_pos_carrito.selection()
        if not seleccion: return
        id_sel = self.tabla_pos_carrito.item(seleccion)['values'][0]
        id_real = str(id_sel).replace("[", "").replace("]", "")
        
        for item in self.carrito:
            if str(item['id']) == id_real:
                if 'stock_max' in item and item['cantidad'] < item['stock_max']:
                    item['cantidad'] += 1
                    self.actualizar_tabla_carrito_visual()
                else:
                    messagebox.showwarning("Stock Agotado", "Cantidad máxima física alcanzada para este ítem.")
                break

    def __init__(self, parent, db, app):
        super().__init__(parent, fg_color='transparent')
        self.pack(fill='both', expand=True, padx=StyleConfig.padding_global, pady=StyleConfig.padding_global)
        self.db = db
        self.app = app
        
        if not hasattr(self, 'carrito'):
            self.carrito = []

        titulo = ctk.CTkLabel(self, text="TERMINAL POS: PUNTO DE VENTA", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=StyleConfig.font_title[1], weight=StyleConfig.font_title[2]))
        titulo.pack(pady=(0, 20), anchor="w")

        pos_frame = ctk.CTkFrame(self, fg_color="transparent")
        pos_frame.pack(fill="both", expand=True)
        pos_frame.grid_columnconfigure(0, weight=6) # 60% Búsqueda
        pos_frame.grid_columnconfigure(1, weight=4) # 40% Cobro
        pos_frame.grid_rowconfigure(0, weight=1)

        boveda_style = {
            "fg_color": StyleConfig.bg_surface,
            "border_color": StyleConfig.border_subtle,
            "border_width": StyleConfig.border_width,
            "corner_radius": StyleConfig.corner_radius_large
        }

        # --- PANEL IZQUIERDO: BUSCADOR ---
        izq_frame = ctk.CTkFrame(pos_frame, **boveda_style)
        izq_frame.grid(row=0, column=0, sticky="nsew", padx=(0,10), ipadx=10, ipady=10)

        ctk.CTkLabel(izq_frame, text="// FILTRO DE CATÁLOGO", font=ctk.CTkFont(family=StyleConfig.font_subtitle[0], size=14, weight="bold"), text_color=StyleConfig.text_muted).pack(pady=(10,5), anchor="w", padx=20)
        
        buscador_frame = ctk.CTkFrame(izq_frame, fg_color="transparent")
        buscador_frame.pack(fill="x", pady=5, padx=20)
        
        self.entry_buscar_pos = ctk.CTkEntry(
            buscador_frame, 
            placeholder_text="ID Comercial o Descripción...", 
            width=350, height=40,
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14),
            fg_color=StyleConfig.bg_base,
            border_color=StyleConfig.accent_primary,
            text_color=StyleConfig.text_main,
            corner_radius=StyleConfig.corner_radius_small
        )
        self.entry_buscar_pos.pack(side="left", fill="x", expand=True)
        self.entry_buscar_pos.bind("<KeyRelease>", self.filtrar_productos_pos)

        cols_busqueda = ("ID", "Nombre", "Categoría", "PVP", "Stock")
        self.tabla_pos_busqueda = ttk.Treeview(izq_frame, columns=cols_busqueda, show="headings")
        for col in cols_busqueda:
            if col in ["PVP", "Stock"]:
                self.tabla_pos_busqueda.heading(col, text=col, anchor="e")
                self.tabla_pos_busqueda.column(col, anchor="e", width=80)
            else:
                self.tabla_pos_busqueda.heading(col, text=col, anchor="w")
                if col == "Nombre": self.tabla_pos_busqueda.column(col, anchor="w", width=200)
                else: self.tabla_pos_busqueda.column(col, anchor="w", width=80)
                
        self.tabla_pos_busqueda.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        self.tabla_pos_busqueda.bind("<Double-1>", self.agregar_al_carrito)
        
        ctk.CTkLabel(izq_frame, text="*Doble Clic para Agregar a la Pila*", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=10), text_color=StyleConfig.text_muted).pack(side="bottom", pady=5, padx=20, anchor="e")

        # --- PANEL DERECHO: CLIENTE Y CARRITO ---
        der_frame = ctk.CTkFrame(pos_frame, **boveda_style)
        der_frame.grid(row=0, column=1, sticky="nsew", ipadx=10, ipady=10)

        # 1. Identificador Cliente
        ctk.CTkLabel(der_frame, text="// IDENTIFICACIÓN DEL COMPRADOR", font=ctk.CTkFont(family=StyleConfig.font_subtitle[0], size=14, weight="bold"), text_color=StyleConfig.text_muted).pack(pady=(10,5), anchor="w", padx=20)
        
        cliente_frame = ctk.CTkFrame(der_frame, fg_color="transparent")
        cliente_frame.pack(fill="x", padx=20)
        
        self.pos_cedula = ctk.CTkEntry(
            cliente_frame, 
            placeholder_text="ID / CÉDULA",
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14),
            fg_color=StyleConfig.bg_base,
            border_color=StyleConfig.border_subtle,
            text_color=StyleConfig.text_main,
            corner_radius=StyleConfig.corner_radius_small,
            height=40
        )
        self.pos_cedula.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_validar_cliente = ctk.CTkButton(
            cliente_frame, 
            text="VERIFICAR", 
            fg_color=StyleConfig.bg_base,
            border_color=StyleConfig.border_subtle,
            border_width=1,
            hover_color=StyleConfig.border_subtle,
            text_color=StyleConfig.text_main,
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            command=self.validar_cliente_pos,
            height=40
        )
        self.btn_validar_cliente.pack(side="right")

        # 2. Checklist Industrial (Carrito)
        ctk.CTkLabel(der_frame, text="// CHECKLIST DE SALIDA", font=ctk.CTkFont(family=StyleConfig.font_subtitle[0], size=14, weight="bold"), text_color=StyleConfig.text_muted).pack(pady=(20,5), anchor="w", padx=20)
        
        botones_carrito_frame = ctk.CTkFrame(der_frame, fg_color="transparent")
        botones_carrito_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(botones_carrito_frame, text="🗑️", width=40, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=16), fg_color=StyleConfig.bg_surface, border_color=StyleConfig.accent_danger, border_width=1, hover_color="#881337", text_color=StyleConfig.accent_danger, command=self.eliminar_del_carrito).pack(side="left", padx=2)
        ctk.CTkButton(botones_carrito_frame, text="➖", width=40, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=16), fg_color=StyleConfig.bg_surface, border_color=StyleConfig.accent_primary, border_width=1, hover_color=StyleConfig.border_subtle, text_color=StyleConfig.text_main, command=self.restar_unidad_carrito).pack(side="left", padx=2)
        ctk.CTkButton(botones_carrito_frame, text="➕", width=40, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=16), fg_color=StyleConfig.bg_surface, border_color=StyleConfig.accent_primary, border_width=1, hover_color=StyleConfig.border_subtle, text_color=StyleConfig.text_main, command=self.sumar_unidad_carrito).pack(side="left", padx=2)
        ctk.CTkButton(botones_carrito_frame, text="LIMPIAR CAJA", width=120, fg_color=StyleConfig.bg_base, font=ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"), hover_color=StyleConfig.border_subtle, text_color=StyleConfig.text_muted, command=self.vaciar_carrito, corner_radius=StyleConfig.corner_radius_small, border_width=1, border_color=StyleConfig.border_subtle).pack(side="right")

        cols_carrito = ("ID", "Desc", "Q", "Sub")
        self.tabla_pos_carrito = ttk.Treeview(der_frame, columns=cols_carrito, show="headings", height=8)
        for col in cols_carrito:
            a = "e" if col in ["Q", "Sub"] else "w"
            w = 30 if col in ["Q"] else 50 if col == "ID" else 150 if col == "Desc" else 70
            self.tabla_pos_carrito.heading(col, text=col, anchor=a)
            self.tabla_pos_carrito.column(col, anchor=a, width=w)
        self.tabla_pos_carrito.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # 3. Resumen y Operador de Pago
        pago_frame = ctk.CTkFrame(der_frame, fg_color=StyleConfig.bg_base, corner_radius=StyleConfig.corner_radius_small)
        pago_frame.pack(fill="x", padx=20, pady=(10, 20), ipadx=10, ipady=10)

        ctk.CTkLabel(pago_frame, text="VÍA TRANSACCIONAL", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12, weight="bold"), text_color=StyleConfig.text_muted).pack(pady=(10,0), anchor="w", padx=15)
        self.opcion_metodo_pago = ctk.CTkOptionMenu(
            pago_frame, 
            values=["EFECTIVO", "TARJETA / POS", "PAGO MÓVIL", "ZELLE"],
            fg_color=StyleConfig.bg_surface,
            button_color=StyleConfig.border_subtle,
            button_hover_color=StyleConfig.accent_primary,
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=13),
            dropdown_font=ctk.CTkFont(family=StyleConfig.font_data[0], size=13)
        )
        self.opcion_metodo_pago.pack(fill="x", padx=15, pady=5)

        self.lbl_desglose_base = ctk.CTkLabel(pago_frame, text="BASE IMPONIBLE:   $0.00", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.accent_success)
        self.lbl_desglose_base.pack(anchor="e", padx=15, pady=(15, 0))
        
        self.lbl_desglose_iva = ctk.CTkLabel(pago_frame, text="IMPUESTO (IVA):   $0.00", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_muted)
        self.lbl_desglose_iva.pack(anchor="e", padx=15)

        self.label_total_dinero = ctk.CTkLabel(pago_frame, text="$0.00", font=ctk.CTkFont(family=StyleConfig.font_data_large[0], size=48, weight="bold"), text_color=StyleConfig.accent_success)
        self.label_total_dinero.pack(anchor="e", padx=15, pady=(5, 10))

        self.btn_procesar_venta = ctk.CTkButton(
            der_frame, 
            text="[ EMITIR FACTURA ]", 
            height=60, 
            font=ctk.CTkFont(family=StyleConfig.font_title[0], size=16, weight="bold"), 
            fg_color=StyleConfig.accent_success, 
            hover_color="#047835",
            text_color="#000000",
            corner_radius=StyleConfig.corner_radius_small,
            command=self.finalizar_venta 
        )
        self.btn_procesar_venta.pack(fill="x", padx=20, side="bottom", pady=20)

    def validar_cliente_pos(self):
        cedula = self.pos_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Atención", "INGRESE un ID válido para verificar en la base de datos.")
            return

        cliente = self.db.buscar_cliente(cedula) 
        
        if cliente:
            messagebox.showinfo("Cliente Autorizado", f"OPERADOR ENCONTRADO:\n{cliente[1]}")
        else:
            if messagebox.askyesno("Registro Ausente", "ID no listada en el sistema. ¿Registrar nueva entidad ahora?"):
                self.abrir_ventana_registro_rapido(cedula)
    
    def abrir_ventana_registro_rapido(self, cedula_inicial):
        ventana_reg = ctk.CTkToplevel(self.app)
        ventana_reg.title("Alta Rápida")
        ventana_reg.geometry("400x350")
        ventana_reg.configure(fg_color="#141416")
        ventana_reg.attributes('-topmost', True) 
        
        ctk.CTkLabel(ventana_reg, text="NUEVO REGISTRO", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=18, weight="bold"), text_color=StyleConfig.text_main).pack(pady=20)
        
        entry_cfg = {
            "font": ctk.CTkFont(family=StyleConfig.font_data[0], size=13),
            "fg_color": StyleConfig.bg_surface,
            "border_color": StyleConfig.border_subtle,
            "text_color": StyleConfig.text_main,
            "corner_radius": 15,
            "height": 40
        }

        entry_ced = ctk.CTkEntry(ventana_reg, **entry_cfg)
        entry_ced.insert(0, cedula_inicial) 
        entry_ced.pack(pady=10, padx=30, fill="x")
        
        entry_nom = ctk.CTkEntry(ventana_reg, placeholder_text="NOMBRE COMPLETO", **entry_cfg)
        entry_nom.pack(pady=10, padx=30, fill="x")
        
        entry_tel = ctk.CTkEntry(ventana_reg, placeholder_text="CÓD. TELÉFONO TÉCNICO", **entry_cfg)
        entry_tel.pack(pady=10, padx=30, fill="x")
        
        def guardar_rapido():
            c = entry_ced.get().strip()
            n = entry_nom.get().title().strip()
            t = entry_tel.get().strip()
            
            if not c or not n:
                messagebox.showwarning("Denegado", "Cédula y Nombre son directivos obligatorios.", parent=ventana_reg)
                return
            if t and not t.isdigit():
                messagebox.showerror("Error de Formato", "El formato numérico para el teléfono es incorrecto.", parent=ventana_reg)
                return
                
            if self.db.registrar_cliente(c, n, t, ""):
                messagebox.showinfo("Éxito", "Nueva entidad archivada de manera segura.", parent=ventana_reg)
                ventana_reg.destroy() 
            else:
                messagebox.showerror("Denegado", "Colisión: La Cédula/ID ya está operando en la base.", parent=ventana_reg)

        ctk.CTkButton(ventana_reg, text="CONFIRMAR ALTA", font=ctk.CTkFont(family=StyleConfig.font_button[0], weight="bold"), fg_color=StyleConfig.accent_primary, text_color="#000", hover_color="#EAB308", corner_radius=15, command=guardar_rapido, height=45).pack(pady=20, padx=30, fill="x")

    def actualizar_tabla_carrito_visual(self):
        for item in self.tabla_pos_carrito.get_children():
            self.tabla_pos_carrito.delete(item)
            
        subtotal_general = 0
        for p in self.carrito:
            subtotal = p['precio'] * p['cantidad']
            subtotal_general += subtotal
            nombre_corto = p['nombre'] if len(p['nombre']) < 15 else p['nombre'][:12] + "..."
            self.tabla_pos_carrito.insert("", "end", values=(f"[{p['id']}]", nombre_corto, p['cantidad'], f"${subtotal:.2f}"))
        
        porcentaje_iva = self.db.obtener_iva()
        total = subtotal_general
        base_imponible = total / (1 + (porcentaje_iva / 100.0))
        monto_iva = total - base_imponible

        self.lbl_desglose_base.configure(text=f"BASE IMPONIBLE:   ${base_imponible:>8.2f}")
        self.lbl_desglose_iva.configure(text=f"IMPUESTO (IVA):   ${monto_iva:>8.2f}")
        self.label_total_dinero.configure(text=f"${total:.2f}")

    def filtrar_productos_pos(self, event=None):
        criterio = self.entry_buscar_pos.get().strip()
        for item in self.tabla_pos_busqueda.get_children():
            self.tabla_pos_busqueda.delete(item)
        
        if len(criterio) > 0:
            productos = self.db.buscar_productos_filtro(criterio)
            for p in productos:
                self.tabla_pos_busqueda.insert("", "end", values=(p[0], p[1].upper(), p[2], f"${p[3]:.2f}", p[4], p[5]))

    def finalizar_venta(self):
        id_cliente = self.pos_cedula.get().strip()
        
        if not id_cliente:
            messagebox.showwarning("Operación Abortada", "REQUERIDO: Identificador de operador/cliente nulo.")
            return
        if not self.carrito:
            messagebox.showwarning("Operación Abortada", "El checklist de salida no tiene transbordos listos (O está vacío).")
            return

        metodo = self.opcion_metodo_pago.get()
        lista_productos = [(p['id'], p['cantidad']) for p in self.carrito]
        
        resultado = self.db.registrar_venta(id_cliente, lista_productos, metodo)
        
        if type(resultado) is dict and resultado.get("exito"):
            resultado["carrito_detalle"] = self.carrito
            cliente_info = self.db.buscar_cliente(id_cliente)
            pdf_path = generar_pdf_factura(resultado, cliente_info)
            messagebox.showinfo("Transacción Asegurada", f"Venta realizada exitosamente.\n\nFACTURA DIGITAL GUARDADA EN:\n{pdf_path}")
            self.carrito = [] 
            self.actualizar_tabla_carrito_visual() 
            self.pos_cedula.delete(0, 'end')
        else:
            msg = resultado.get("error") if type(resultado) is dict else "Desconocido"
            messagebox.showerror("Error Fatal del Banco", f"La Transacción fue rechazada.\n\nDETALLE TÉCNICO: {msg}")
        pass
