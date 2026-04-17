import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pytz
import os
import csv
from Inventario import Inventario, Producto
from generador_pdf import generar_pdf_factura, generar_pdf_cierre_caja
from style_config import StyleConfig

class ClientesView(ctk.CTkFrame):
    def accion_registrar_cliente(self):
        cedula = self.entry_cedula.get().strip()
        nombre = self.entry_nombre.get().title().strip()
        telefono = self.entry_tel.get().strip()
        email = "N/A" 

        if not cedula or not nombre or not telefono:
            messagebox.showwarning("Faltan Datos", "Todos los campos de identificación son obligatorios.")
            return

        if not telefono.isdigit():
            messagebox.showerror("Error de Formato", "El número de teléfono solo debe contener numerales.")
            return

        exito = self.db.registrar_cliente(cedula, nombre, telefono, email)
        
        if exito:
            messagebox.showinfo("Registro Exitoso", "El Cliente fué registrado exitosamente.")
            self.entry_cedula.delete(0, 'end')
            self.entry_nombre.delete(0, 'end')
            self.entry_tel.delete(0, 'end')
            self.actualizar_tabla_clientes()
        else:
            messagebox.showerror("Colisión Detectada", "No se pudo registrar. La ID / Cédula ya existe en la base.")

    def __init__(self, parent, db, app):
        super().__init__(parent, fg_color='transparent')
        self.pack(fill='both', expand=True, padx=StyleConfig.padding_global, pady=StyleConfig.padding_global)
        self.db = db
        self.app = app
        
        titulo = ctk.CTkLabel(self, text="GESTIÓN DE CLIENTES", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=StyleConfig.font_title[1], weight=StyleConfig.font_title[2]), text_color=StyleConfig.text_main)
        titulo.pack(pady=(0, 20), anchor="w")

        # --- BÓVEDA DE REGISTRO ---
        form_frame = ctk.CTkFrame(
            self, 
            fg_color=StyleConfig.bg_surface,
            border_width=StyleConfig.border_width,
            border_color=StyleConfig.border_subtle,
            corner_radius=StyleConfig.corner_radius_small
        )
        form_frame.pack(fill="x", pady=(0, 20), ipadx=10, ipady=10)

        ctk.CTkLabel(form_frame, text="REGISTRO DE NUEVO CLIENTE", font=ctk.CTkFont(family=StyleConfig.font_subtitle[0], size=14, weight="bold"), text_color=StyleConfig.text_muted).grid(row=0, column=0, columnspan=4, pady=(5, 15), padx=10, sticky="w")

        entry_cfg = {
            "font": ctk.CTkFont(family=StyleConfig.font_data[0], size=13),
            "fg_color": StyleConfig.bg_base,
            "border_color": StyleConfig.border_subtle,
            "text_color": StyleConfig.text_main,
            "corner_radius": StyleConfig.corner_radius_small,
            "height": 35
        }

        self.entry_cedula = ctk.CTkEntry(form_frame, placeholder_text="ID / CÉDULA / RIF", width=150, **entry_cfg)
        self.entry_cedula.grid(row=1, column=0, padx=10, pady=5)
        
        self.entry_nombre = ctk.CTkEntry(form_frame, placeholder_text="NOMBRE COMPLETO", width=250, **entry_cfg)
        self.entry_nombre.grid(row=1, column=1, padx=10, pady=5)

        self.entry_tel = ctk.CTkEntry(form_frame, placeholder_text="TELÉFONO DE CONTACTO", width=180, **entry_cfg)
        self.entry_tel.grid(row=1, column=2, padx=10, pady=5)

        btn_guardar = ctk.CTkButton(
            form_frame, 
            text="REGISTRAR", 
            command=self.accion_registrar_cliente,
            fg_color="#FACC15",
            hover_color="#b59619",
            text_color="#000000",
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            corner_radius=StyleConfig.corner_radius_small,
            height=35
        )
        btn_guardar.grid(row=1, column=3, padx=(20, 5), pady=10)
        
        btn_config_sup = {
            "font": ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            "height": 35,
            "corner_radius": StyleConfig.corner_radius_small,
            "border_width": 1,
            "border_color": StyleConfig.border_subtle
        }
        
        ctk.CTkButton(form_frame, text="EDITAR", fg_color=StyleConfig.bg_surface, text_color=StyleConfig.text_main, command=self.editar_cliente_gui, **btn_config_sup).grid(row=1, column=4, padx=5, pady=10)
        ctk.CTkButton(form_frame, text="ELIMINAR", fg_color=StyleConfig.bg_surface, text_color=StyleConfig.accent_danger, hover_color="#881337", border_color=StyleConfig.accent_danger, command=self.borrar_cliente_gui, font=btn_config_sup["font"], height=35, corner_radius=StyleConfig.corner_radius_small, border_width=1).grid(row=1, column=5, padx=(5, 10), pady=10)

        # --- PANOPTICO DE ENTIDADES (Tabla) ---
        ctk.CTkLabel(self, text="DIRECTORIO DE CLIENTES", font=ctk.CTkFont(family=StyleConfig.font_subtitle[0], size=14, weight="bold"), text_color=StyleConfig.text_muted).pack(anchor="w", pady=(0,5))
        columns = ("ID", "Nombre", "Teléfono", "Email")
        self.tabla_clientes = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col in columns:
            self.tabla_clientes.heading(col, text=col, anchor="w")
            if col == "Nombre": self.tabla_clientes.column(col, anchor="w", width=300)
            else: self.tabla_clientes.column(col, anchor="w", width=150)
            
        self.tabla_clientes.pack(fill="both", expand=True, pady=(0, 10))
        self.tabla_clientes.bind("<Double-1>", self.abrir_historial_cliente)
        
        # --- PANEL DE ACCIONES ---
        acciones_frame = ctk.CTkFrame(self, fg_color="transparent")
        acciones_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(acciones_frame, text="*Doble clic en tabla para ver historial transaccional", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=10), text_color=StyleConfig.text_muted).pack(side="right")

        self.actualizar_tabla_clientes()

    def actualizar_tabla_clientes(self):
        for item in self.tabla_clientes.get_children():
            self.tabla_clientes.delete(item)
        
        clientes = self.db.listar_clientes()
        for cliente in clientes:
            self.tabla_clientes.insert("", "end", values=cliente)

    def borrar_cliente_gui(self):
        seleccion = self.tabla_clientes.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un cliente del directorio para revocar.")
            return
        cedula = self.tabla_clientes.item(seleccion)['values'][0]
        nombre = self.tabla_clientes.item(seleccion)['values'][1]

        if messagebox.askyesno("Revuelta Crítica", f"¿ELIMINAR definitivamente a la entidad {nombre} (ID: {cedula})?"):
            try:
                exito = self.db.eliminar_cliente(cedula)
                if exito:
                    messagebox.showinfo("Purga Exitosa", "El Cliente fué eliminado exitosamente.")
                    self.actualizar_tabla_clientes()
                else:
                    messagebox.showerror("Error", "El motor declinó la eliminación de la entidad.")
            except ValueError as e:
                messagebox.showerror("Excepción", str(e))
            except Exception as e:
                messagebox.showerror("Error Crítico", "Fallo general de borrado.")

    def abrir_historial_cliente(self, event):
        seleccion = self.tabla_clientes.selection()
        if not seleccion: return
        
        cedula = self.tabla_clientes.item(seleccion)['values'][0]
        nombre = self.tabla_clientes.item(seleccion)['values'][1]
        
        ventana_hist = ctk.CTkToplevel(self.app)
        ventana_hist.title(f"Bitácora de Salida: {nombre}")
        ventana_hist.geometry("700x550")
        ventana_hist.configure(fg_color=StyleConfig.bg_base)
        ventana_hist.attributes('-topmost', True)

        ctk.CTkLabel(ventana_hist, text=f"HISTORIAL TRANSACCIONAL: {nombre}", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=18, weight="bold"), text_color=StyleConfig.accent_primary).pack(pady=(20, 10))

        scroll_frame = ctk.CTkScrollableFrame(ventana_hist, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        compras = self.db.obtener_historial_cliente(cedula)
        
        if not compras:
            ctk.CTkLabel(scroll_frame, text="Sin transbordos registrados para esta identidad.", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14), text_color=StyleConfig.text_muted).pack(pady=40)
            return

        for venta in compras:
            card = ctk.CTkFrame(scroll_frame, corner_radius=StyleConfig.corner_radius_small, fg_color=StyleConfig.bg_surface, border_color=StyleConfig.border_subtle, border_width=1)
            card.pack(fill="x", pady=10, padx=5)

            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            fecha_lista = venta['fecha'].split()[0].split('-')
            fecha_format = f"{fecha_lista[2]}-{fecha_lista[1]}-{fecha_lista[0]}" if len(fecha_lista) == 3 else venta['fecha']
            ctk.CTkLabel(header_frame, text=f"OPERACIÓN: {fecha_format}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14, weight="bold"), text_color=StyleConfig.text_main).pack(side="left")
            ctk.CTkLabel(header_frame, text=f" VIA: {venta.get('metodo_pago', 'N/A')}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_muted).pack(side="left", padx=15)
            ctk.CTkLabel(header_frame, text=f"SALDO: ${venta['total']:.2f}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=16, weight="bold"), text_color=StyleConfig.accent_success).pack(side="right")

            separador = ctk.CTkFrame(card, height=1, fg_color=StyleConfig.border_subtle)
            separador.pack(fill="x", padx=15, pady=10)

            for p in venta['productos']:
                ctk.CTkLabel(card, text=f"► {p['nombre'].upper()}   [ x{p['cantidad']} ]", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_main).pack(anchor="w", padx=25, pady=2)
                ctk.CTkLabel(card, text=f"${p['subtotal']:.2f}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_muted).pack(anchor="e", padx=25, pady=(0, 5))
            
            ctk.CTkLabel(card, text="", height=5).pack()

    def editar_cliente_gui(self):
        seleccion = self.tabla_clientes.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una entidad para someter a revisión.")
            return

        cedula = self.tabla_clientes.item(seleccion)['values'][0]
        nombre = self.tabla_clientes.item(seleccion)['values'][1]
        telefono = self.tabla_clientes.item(seleccion)['values'][2]
        email = self.tabla_clientes.item(seleccion)['values'][3]

        ventana_ed = ctk.CTkToplevel(self.app)
        ventana_ed.title("Re-configuración")
        ventana_ed.geometry("400x400")
        ventana_ed.configure(fg_color=StyleConfig.bg_base)
        ventana_ed.attributes('-topmost', True)

        ctk.CTkLabel(ventana_ed, text=f"MODIFICAR ENTIDAD: ID {cedula}", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=18, weight="bold"), text_color=StyleConfig.text_main).pack(pady=(20,10))

        entry_cfg = {
            "font": ctk.CTkFont(family=StyleConfig.font_data[0], size=13),
            "fg_color": StyleConfig.bg_surface,
            "border_color": StyleConfig.border_subtle,
            "text_color": StyleConfig.text_main,
            "corner_radius": StyleConfig.corner_radius_small,
            "height": 40
        }

        entry_ced = ctk.CTkEntry(ventana_ed, **entry_cfg)
        entry_ced.insert(0, str(cedula))
        entry_ced.configure(state="disabled", text_color=StyleConfig.text_muted)
        entry_ced.pack(pady=10, padx=30, fill="x")

        entry_nom = ctk.CTkEntry(ventana_ed, **entry_cfg)
        entry_nom.insert(0, str(nombre))
        entry_nom.configure(state="disabled", text_color=StyleConfig.text_muted)
        entry_nom.pack(pady=10, padx=30, fill="x")

        entry_tel = ctk.CTkEntry(ventana_ed, **entry_cfg)
        entry_tel.insert(0, str(telefono) if str(telefono) != 'None' else '')
        entry_tel.pack(pady=10, padx=30, fill="x")

        entry_email = ctk.CTkEntry(ventana_ed, **entry_cfg)
        entry_email.insert(0, str(email) if str(email) != 'None' and str(email) != 'N/A' else '')
        entry_email.pack(pady=10, padx=30, fill="x")

        def guardar_cambios():
            t = entry_tel.get().strip()
            e = entry_email.get().strip()
            
            if t and not t.isdigit():
                messagebox.showerror("Error", "El teléfono carece de formato numérico puro.", parent=ventana_ed)
                return
                
            if self.db.actualizar_cliente(cedula, t, e if e else "N/A"):
                messagebox.showinfo("Éxito", "Perfil Operativo Actualizado.", parent=ventana_ed)
                self.actualizar_tabla_clientes()
                ventana_ed.destroy()
            else:
                messagebox.showerror("Fallo de Motor", "Rechazado por el motor de base de datos.", parent=ventana_ed)

        ctk.CTkButton(ventana_ed, text="INCRUSTAR CAMBIOS", font=ctk.CTkFont(family=StyleConfig.font_button[0], weight="bold"), fg_color=StyleConfig.accent_primary, text_color="#000", hover_color="#EAB308", command=guardar_cambios, height=45).pack(pady=20, padx=30, fill="x")
