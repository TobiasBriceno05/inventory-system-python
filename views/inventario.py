import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pytz
import os
import csv
from Inventario import Inventario, Producto
from generador_pdf import generar_pdf_factura, generar_pdf_cierre_caja
from style_config import StyleConfig

class InventarioView(ctk.CTkFrame):
    def accion_registrar_producto(self):
        try:
            id_p = self.entry_id_p.get().strip()
            nom = self.entry_nom_p.get().strip()
            cat = self.entry_cat_p.get().strip()
            
            pre_str = self.entry_pre_p.get().strip()
            costo_str = self.entry_costo_p.get().strip()
            can_str = self.entry_can_p.get().strip()

            if not id_p or not nom or not cat or not pre_str or not costo_str or not can_str:
                messagebox.showwarning("Faltan Datos", "Todos los campos son obligatorios.")
                return

            pre = float(pre_str)
            costo = float(costo_str)
            can = int(can_str)

            iva = self.db.obtener_iva()
            precio_sin_iva = pre / (1 + (iva / 100.0))
            if precio_sin_iva <= costo:
                messagebox.showerror("Error de Rentabilidad", f"El precio de venta sin IVA (${precio_sin_iva:.2f}) debe ser mayor al costo (${costo:.2f}).")
                return

            nuevo_p = Producto(id_p, nom, cat, pre, costo, can)

            if self.db.agregar_producto(nuevo_p):
                messagebox.showinfo("Éxito", f"Producto {nom} guardado en el sistema.")
                self.actualizar_tabla_inventario()
                self.entry_id_p.delete(0, 'end')
                self.entry_nom_p.delete(0, 'end')
                self.entry_cat_p.delete(0, 'end')
                self.entry_pre_p.delete(0, 'end')
                self.entry_costo_p.delete(0, 'end')
                self.entry_can_p.delete(0, 'end')
            else:
                messagebox.showerror("Error", "El ID de producto ya existe.")

        except ValueError:
            messagebox.showerror("Error de Formato", "Precio y Costo deben ser numéricos. Stock debe ser entero.")

    def borrar_producto_gui(self):
        seleccion = self.tabla_inv.selection()
        if not seleccion: 
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla para eliminar.")
            return
        id_p = self.tabla_inv.item(seleccion)['values'][0]
        nom = self.tabla_inv.item(seleccion)['values'][1]
        if messagebox.askyesno("Confirmar Acción", f"¿ELIMINAR DEFINITIVAMENTE el producto: {nom}?"):
            self.db.eliminar_producto(id_p)
            messagebox.showinfo("Éxito", "Proceso de eliminación ejecutado.")
            self.actualizar_tabla_inventario()

    def _crear_dialogo(self, titulo, label_texto, callback, validacion="float", default_text=""):
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
        if default_text:
            entrada.insert(0, str(default_text))
        entrada.pack(pady=10)
        
        def procesar():
            val = entrada.get().strip()
            if not val:
                messagebox.showwarning("Vacío", "El campo no puede estar vacío.", parent=ventana_dialog)
                return
            if validacion == "float":
                try: float(val)
                except ValueError: return messagebox.showerror("Error", "Debe ser numérico", parent=ventana_dialog)
            elif validacion == "int":
                try: int(val)
                except ValueError: return messagebox.showerror("Error", "Debe ser entero", parent=ventana_dialog)
            
            ventana_dialog.destroy()
            callback(val)
            
        btn = ctk.CTkButton(ventana_dialog, text="CONFIRMAR", command=procesar, fg_color=StyleConfig.accent_primary, text_color="#000", font=ctk.CTkFont(family=StyleConfig.font_button[0], weight="bold"), height=40, corner_radius=15, hover_color="#EAB308")
        btn.pack(pady=10)

    def _crear_dialogo_doble(self, titulo, callback):
        ventana_dialog = ctk.CTkToplevel(self.app)
        ventana_dialog.title(titulo)
        ventana_dialog.geometry("450x300")
        ventana_dialog.configure(fg_color="#141416")
        ventana_dialog.attributes('-topmost', True)
        
        ctk.CTkLabel(ventana_dialog, text=titulo.upper(), font=ctk.CTkFont(family=StyleConfig.font_title[0], size=16, weight="bold"), text_color=StyleConfig.accent_primary).pack(pady=(20, 10))
        
        entr_cat = ctk.CTkEntry(ventana_dialog, placeholder_text="Nombre de Categoría", width=250, height=40, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14), fg_color=StyleConfig.bg_base, border_color=StyleConfig.border_subtle, corner_radius=15)
        entr_cat.pack(pady=(10, 5))

        entr_porc = ctk.CTkEntry(ventana_dialog, placeholder_text="% de Ajuste (ej: 10 o -5)", width=250, height=40, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14), fg_color=StyleConfig.bg_base, border_color=StyleConfig.border_subtle, corner_radius=15)
        entr_porc.pack(pady=5)
        
        def procesar():
            cat = entr_cat.get().strip()
            porc_str = entr_porc.get().strip()
            if not cat or not porc_str:
                return messagebox.showwarning("Faltan Datos", "Debe llenar ambos campos.", parent=ventana_dialog)
            try:
                porc = float(porc_str)
                ventana_dialog.destroy()
                callback(cat, porc)
            except ValueError:
                messagebox.showerror("Error", "El porcentaje debe ser numérico.", parent=ventana_dialog)
            
        ctk.CTkButton(ventana_dialog, text="APLICAR AJUSTE", command=procesar, fg_color=StyleConfig.accent_primary, text_color="#000", font=ctk.CTkFont(family=StyleConfig.font_button[0], weight="bold"), height=40, corner_radius=15, hover_color="#EAB308").pack(pady=15)


    def ajustar_precios_gui(self):
        def on_confirm(categoria, porcentaje):
            if self.db.actualizar_precios_categoria(categoria, porcentaje):
                messagebox.showinfo("Éxito", f"Precios actualizados en un {porcentaje}% para {categoria}.")
                self.actualizar_tabla_inventario()
        self._crear_dialogo_doble("Ajuste Masivo de Precio", on_confirm)

    def modificar_precio_producto_gui(self):
        seleccion = self.tabla_inv.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla.")
            return
        id_p = self.tabla_inv.item(seleccion)['values'][0]
        costo_p_str = str(self.tabla_inv.item(seleccion)['values'][4]).replace('$', '').replace(',', '')
        costo_p = float(costo_p_str)
        
        def on_confirm(nuevo_precio_str):
            nuevo_precio = float(nuevo_precio_str)
            if nuevo_precio < 0:
                messagebox.showerror("Error", "El precio no puede ser negativo.")
                return
            
            iva = self.db.obtener_iva()
            precio_sin_iva = nuevo_precio / (1 + (iva / 100.0))
            if precio_sin_iva <= costo_p:
                messagebox.showerror("Error de Rentabilidad", f"El precio de venta sin IVA (${precio_sin_iva:.2f}) debe ser mayor al costo (${costo_p:.2f}).")
                return

            self.db.actualizar_precio_producto(id_p, nuevo_precio)
            messagebox.showinfo("Éxito", "Precio modificado correctamente.")
            self.actualizar_tabla_inventario()

        self._crear_dialogo("Modificar Precio Singular", f"Nuevo PRECIO (PVP) para ID {id_p}:", on_confirm, validacion="float")
    
    def __init__(self, parent, db, app):
        super().__init__(parent, fg_color='transparent')
        self.pack(fill='both', expand=True, padx=StyleConfig.padding_global, pady=StyleConfig.padding_global)
        self.db = db
        self.app = app
        
        # --- HEADER PRINCIPAL ---
        main_header = ctk.CTkFrame(self, fg_color="transparent")
        main_header.pack(fill="x", pady=(0, 10))

        titulo = ctk.CTkLabel(
            main_header, 
            text="GESTIÓN DE INVENTARIO", 
            font=ctk.CTkFont(family=StyleConfig.font_title[0], size=StyleConfig.font_title[1], weight=StyleConfig.font_title[2]),
            text_color=StyleConfig.text_main
        )
        titulo.pack(side="left")

        btn_config_sup = {
            "font": ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            "height": 35,
            "corner_radius": StyleConfig.corner_radius_small,
            "border_width": 1,
            "border_color": StyleConfig.border_subtle
        }
        
        ctk.CTkButton(main_header, text="[ EXPORTAR CSV ]", fg_color=StyleConfig.bg_surface, hover_color=StyleConfig.border_subtle, 
                      text_color=StyleConfig.text_main, command=self.exportar_inventario_csv, **btn_config_sup).pack(side="right")

        # --- HEADER CONTROLES (Reorganización Solicitada) ---
        header_acciones = ctk.CTkFrame(self, fg_color="transparent")
        header_acciones.pack(fill="x", pady=(0, 20))

        # Registrar (Acento Azul), Eliminar (Rojo), ModPrecio, AgStock, QStock, AjCategoria, Tasa IVA.
        fnt = ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold")
        
        ctk.CTkButton(header_acciones, text="REGISTRAR", fg_color="#FACC15", text_color="#000000", hover_color="#b59619", corner_radius=StyleConfig.corner_radius_small, font=fnt, height=35, command=self.accion_registrar_producto).pack(side="left", padx=(0, 10))
        ctk.CTkButton(header_acciones, text="ELIMINAR", fg_color=StyleConfig.bg_surface, text_color=StyleConfig.accent_danger, hover_color="#881337", border_color=StyleConfig.accent_danger, border_width=1, corner_radius=StyleConfig.corner_radius_small, font=fnt, height=35, command=self.borrar_producto_gui).pack(side="left", padx=10)
        ctk.CTkButton(header_acciones, text="MODIFICAR PRECIO", command=self.modificar_precio_producto_gui, fg_color=StyleConfig.bg_surface, text_color=StyleConfig.text_main, **btn_config_sup).pack(side="left", padx=10)
        ctk.CTkButton(header_acciones, text="AGREGAR STOCK", command=self.agregar_stock_gui, fg_color=StyleConfig.bg_surface, text_color=StyleConfig.accent_success, **btn_config_sup).pack(side="left", padx=10)
        ctk.CTkButton(header_acciones, text="QUITAR STOCK", command=self.retirar_stock_gui, fg_color=StyleConfig.bg_surface, text_color=StyleConfig.accent_primary, **btn_config_sup).pack(side="left", padx=10)
        ctk.CTkButton(header_acciones, text="AJUSTE CATEGORÍA", command=self.ajustar_precios_gui, fg_color=StyleConfig.bg_surface, text_color=StyleConfig.text_main, **btn_config_sup).pack(side="left", padx=10)

        iva_actual = self.db.obtener_iva()
        self.btn_ajuste_iva = ctk.CTkButton(header_acciones, text=f"TASA IVA: {iva_actual}%", command=self.actualizar_iva_gui, fg_color=StyleConfig.bg_surface, text_color=StyleConfig.text_muted, **btn_config_sup)
        self.btn_ajuste_iva.pack(side="right")


        # --- BÓVEDA DE INGRESO (FORMULARIO CAJA) ---
        form_frame = ctk.CTkFrame(
            self, 
            fg_color=StyleConfig.bg_surface,
            border_width=StyleConfig.border_width,
            border_color=StyleConfig.border_subtle,
            corner_radius=StyleConfig.corner_radius_small
        )
        form_frame.pack(fill="x", pady=(0, 20), ipadx=10, ipady=10)

        # Config general inputs
        entry_cfg = {
            "font": ctk.CTkFont(family=StyleConfig.font_data[0], size=12),
            "fg_color": StyleConfig.bg_base,
            "border_color": StyleConfig.border_subtle,
            "text_color": StyleConfig.text_main,
            "corner_radius": StyleConfig.corner_radius_small,
            "height": 35
        }

        self.entry_id_p = ctk.CTkEntry(form_frame, placeholder_text="ID Prod.", width=120, **entry_cfg)
        self.entry_id_p.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.entry_nom_p = ctk.CTkEntry(form_frame, placeholder_text="Nombre Comercial", width=250, **entry_cfg)
        self.entry_nom_p.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.entry_cat_p = ctk.CTkEntry(form_frame, placeholder_text="Categoría", width=150, **entry_cfg)
        self.entry_cat_p.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.entry_pre_p = ctk.CTkEntry(form_frame, placeholder_text="PVP ($)", width=100, **entry_cfg)
        self.entry_pre_p.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.entry_costo_p = ctk.CTkEntry(form_frame, placeholder_text="Costo ($)", width=100, **entry_cfg)
        self.entry_costo_p.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.entry_can_p = ctk.CTkEntry(form_frame, placeholder_text="Stock Inic.", width=100, **entry_cfg)
        self.entry_can_p.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        # --- TABLA DE INVENTARIO ---
        columns = ("Código", "Nombre", "Categoría", "Precio", "Costo", "Stock")
        self.tabla_inv = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            if col in ["Precio", "Costo", "Stock"]:
                self.tabla_inv.heading(col, text=col, anchor="e")
                self.tabla_inv.column(col, anchor="e", width=100)
            else:
                self.tabla_inv.heading(col, text=col, anchor="w")
                if col == "Nombre": self.tabla_inv.column(col, anchor="w", width=250)
                if col == "Código": self.tabla_inv.column(col, anchor="w", width=100)
        
        self.tabla_inv.pack(fill="both", expand=True, pady=(0, 10))
        self.actualizar_tabla_inventario() 

    def actualizar_iva_gui(self):
        def on_confirm(nuevo_iva_str):
            nuevo_iva = float(nuevo_iva_str)
            if nuevo_iva < 0:
                messagebox.showerror("Error", "El IVA no puede ser negativo.")
                return
            self.db.actualizar_iva(nuevo_iva)
            messagebox.showinfo("Éxito", "Tasa de IVA actualizada globalmente.")
            self.btn_ajuste_iva.configure(text=f"TASA IVA: {nuevo_iva}%")
        self._crear_dialogo("Configuración de Tasa", "Ingrese el nuevo porcentaje de IVA global (ej: 16):", on_confirm, validacion="float")

    def exportar_inventario_csv(self):
        productos = self.db.listar_productos()
        if not productos:
            messagebox.showwarning("Vacío", "El inventario está vacío.")
            return

        archivo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not archivo: return
        
        try:
            with open(archivo, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Código", "Nombre", "Categoría", "Precio", "Costo", "Stock"])
                for p in productos:
                    writer.writerow(p)
            messagebox.showinfo("Éxito", f"Inventario exportado en:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar: {e}")

    def actualizar_tabla_inventario(self):
        for item in self.tabla_inv.get_children():
            self.tabla_inv.delete(item)
        
        productos = self.db.listar_productos()
        for p in productos:
            row = (p[0], p[1], p[2], f"${p[3]:.2f}", f"${p[4]:.2f}", p[5])
            self.tabla_inv.insert("", "end", values=row)

    def agregar_stock_gui(self):
        seleccion = self.tabla_inv.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un producto.")
            return
        id_p = self.tabla_inv.item(seleccion)['values'][0]
        
        def on_confirm(cant_str):
            cant = int(cant_str)
            if cant <= 0: return
            self.db.agregar_stock(id_p, cant)
            self.actualizar_tabla_inventario()
            
        self._crear_dialogo("Entrada Stock", f"Cantidad a INYECTAR en {id_p}:", on_confirm, validacion="int")

    def retirar_stock_gui(self):
        seleccion = self.tabla_inv.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un producto.")
            return
        id_p = self.tabla_inv.item(seleccion)['values'][0]
        actual = int(self.tabla_inv.item(seleccion)['values'][5])
        
        def on_confirm(cant_str):
            cant = int(cant_str)
            if cant <= 0: return
            if cant > actual:
                messagebox.showerror("Error", f"No puede retirar más del stock físico ({actual}).")
                return
            self.db.quitar_stock(id_p, cant)
            self.actualizar_tabla_inventario()
            
        self._crear_dialogo("Salida Stock", f"Cantidad a RETIRAR de {id_p} (Max {actual}):", on_confirm, validacion="int")