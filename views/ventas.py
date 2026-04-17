import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pytz
import os
import csv
from Inventario import Inventario, Producto
from generador_pdf import generar_pdf_factura, generar_pdf_cierre_caja
from style_config import StyleConfig

class VentasView(ctk.CTkFrame):
    def __init__(self, parent, db, app):
        super().__init__(parent, fg_color='transparent')
        self.pack(fill='both', expand=True, padx=StyleConfig.padding_global, pady=StyleConfig.padding_global)
        self.db = db
        self.app = app
        
        # Header (Titulo y Buscador)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        titulo = ctk.CTkLabel(header_frame, text="REGISTRO TRANSACCIONAL", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=StyleConfig.font_title[1], weight=StyleConfig.font_title[2]), text_color=StyleConfig.text_main)
        titulo.pack(side="left")

        # Buscador
        self.entry_buscar_ventas = ctk.CTkEntry(
            header_frame, 
            width=300, 
            height=40,
            placeholder_text="FILTRO: ID Transacción o Entidad...",
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14),
            fg_color=StyleConfig.bg_base,
            border_color=StyleConfig.border_subtle,
            text_color=StyleConfig.text_main,
            corner_radius=StyleConfig.corner_radius_small
        )
        self.entry_buscar_ventas.pack(side="right")
        self.entry_buscar_ventas.bind("<KeyRelease>", self.filtrar_ventas_historial)

        # Controles y Cierre de caja
        frame_acciones_ven = ctk.CTkFrame(self, fg_color="transparent")
        frame_acciones_ven.pack(fill="x", pady=(0, 10))

        btn_cierre = ctk.CTkButton(
            frame_acciones_ven, 
            text="CERRAR CAJA DIARIA", 
            fg_color=StyleConfig.accent_primary, 
            hover_color="#EAB308", 
            text_color="#000",
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            command=self.generar_cierre_caja_gui,
            height=35,
            corner_radius=StyleConfig.corner_radius_small
        )
        btn_cierre.pack(side="right")

        btn_exportar_ventas = ctk.CTkButton(
            frame_acciones_ven, 
            text="EXPORTAR DUMP (CSV)", 
            fg_color=StyleConfig.bg_surface, 
            hover_color=StyleConfig.border_subtle, 
            text_color=StyleConfig.text_main,
            border_color=StyleConfig.border_subtle,
            border_width=1,
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            command=self.exportar_ventas_csv,
            height=35,
            corner_radius=StyleConfig.corner_radius_small
        )
        btn_exportar_ventas.pack(side="right", padx=10)

        self.scroll_ventas = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_ventas.pack(fill="both", expand=True)

        ventas = self.db.obtener_todas_las_ventas()
        
        if not ventas:
            ctk.CTkLabel(self.scroll_ventas, text="Base de datos vacía. Sin transbordos.", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14), text_color=StyleConfig.text_muted).pack(pady=40)
            return

        self.ventas_renderizadas = {}

        for venta in ventas:
            card = ctk.CTkFrame(self.scroll_ventas, corner_radius=StyleConfig.corner_radius_small, fg_color=StyleConfig.bg_surface, border_color=StyleConfig.border_subtle, border_width=StyleConfig.border_width)
            card.pack(fill="x", pady=5, padx=5)

            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            cliente_info = f"{venta['nombre_cliente']} (ID: {venta['id_cliente']})"
            
            ctk.CTkLabel(header_frame, text=f"RX #{venta['id']}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14, weight="bold"), text_color=StyleConfig.text_muted).pack(side="left", padx=(0, 15))
            
            fecha_lista = venta['fecha'].split()[0].split('-')
            hora_raw = venta['fecha'].split()[1] if len(venta['fecha'].split()) > 1 else "00:00:00"
            hora_fmt = ":".join(hora_raw.split(':')[:2])
            fecha_format = f"{fecha_lista[2]}-{fecha_lista[1]}-{fecha_lista[0]}" if len(fecha_lista) == 3 else venta['fecha'].split()[0]
            
            ctk.CTkLabel(header_frame, text=f"{fecha_format} | {hora_fmt}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14, weight="bold"), text_color=StyleConfig.text_main).pack(side="left", padx=(0, 15))
            ctk.CTkLabel(header_frame, text=f"[{cliente_info}]", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_muted).pack(side="left")
            
            frame_der = ctk.CTkFrame(header_frame, fg_color="transparent")
            frame_der.pack(side="right")
            
            btn_devol = ctk.CTkButton(
                frame_der, 
                text="DEVOLUCIÓN", 
                fg_color=StyleConfig.bg_base, 
                border_color=StyleConfig.accent_danger,
                border_width=1,
                hover_color="#881337", 
                text_color=StyleConfig.accent_danger,
                width=80, 
                height=25, 
                font=ctk.CTkFont(family=StyleConfig.font_button[0], size=11, weight="bold"),
                command=lambda id_v=venta['id']: self.iniciar_proceso_devolucion(id_v),
                corner_radius=StyleConfig.corner_radius_small
            )
            btn_devol.pack(side="left", padx=15)
            
            ctk.CTkLabel(frame_der, text=f"${venta['total']:.2f}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=16, weight="bold"), text_color=StyleConfig.accent_success).pack(side="right")

            separador = ctk.CTkFrame(card, height=1, fg_color=StyleConfig.border_subtle)
            separador.pack(fill="x", padx=15, pady=5)

            for p in venta['productos']:
                ctk.CTkLabel(card, text=f"► {p['nombre'].upper()}  [ QTY: {p['cantidad']} ]   ->   ${p['subtotal']:.2f}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.text_main).pack(anchor="w", padx=25, pady=2)
            
            ctk.CTkLabel(card, text="", height=5).pack()

            self.ventas_renderizadas[venta['id']] = {
                'widget': card,
                'cliente': cliente_info,
            }

    def filtrar_ventas_historial(self, event=None):
        criterio = self.entry_buscar_ventas.get().strip().upper()
        
        for v_id, dict_card in self.ventas_renderizadas.items():
            if (criterio in str(v_id).upper() or 
                criterio in dict_card['cliente'].upper()):
                dict_card['widget'].pack(fill="x", pady=10, padx=5)
            else:
                dict_card['widget'].pack_forget()

    def iniciar_proceso_devolucion(self, id_venta):
        for v in self.db.obtener_todas_las_ventas():
            if v['id'] == id_venta:
                venta = v
                break
        
        ventana_dev = ctk.CTkToplevel(self.app)
        ventana_dev.title(f"Reversión de Saldo - RX #{id_venta}")
        ventana_dev.geometry("500x450")
        ventana_dev.configure(fg_color="#141416")
        ventana_dev.attributes('-topmost', True)
        
        ctk.CTkLabel(ventana_dev, text="PARÁMETROS DE EXTRACCIÓN (QTY)", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=14, weight="bold")).pack(pady=20)
        
        scroll = ctk.CTkScrollableFrame(ventana_dev, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        entradas_dev = {} 
        
        conexion = self.db.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT d.id_producto, p.nombre, d.cantidad, d.precio_unitario FROM detalle_ventas d JOIN productos p ON d.id_producto = p.id WHERE d.id_venta=?", (id_venta,))
        detalles_bd = cursor.fetchall()
        
        for p_bd in detalles_bd:
            id_prod, nom_prod, cant_orig = p_bd[0], p_bd[1], p_bd[2]
            
            cursor.execute("""
                SELECT SUM(dd.cantidad)
                FROM detalle_devoluciones dd
                JOIN devoluciones d ON dd.id_devolucion = d.id
                WHERE d.id_venta = ? AND dd.id_producto = ?
            """, (id_venta, id_prod))
            devueltas_previas = cursor.fetchone()[0] or 0
            
            max_cant = cant_orig - devueltas_previas
            
            row_frame = ctk.CTkFrame(scroll, fg_color=StyleConfig.bg_surface, corner_radius=15)
            row_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row_frame, text=f"► {nom_prod.upper()}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12)).pack(side="left", padx=10, pady=10)
            
            entrada = ctk.CTkEntry(row_frame, width=80, font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), fg_color=StyleConfig.bg_base, border_color=StyleConfig.border_subtle, corner_radius=15)
            
            if max_cant <= 0:
                entrada.insert(0, "VACÍO")
                entrada.configure(state="disabled", text_color=StyleConfig.text_muted)
            else:
                entrada.insert(0, "0")
                ctk.CTkLabel(row_frame, text=f"Max: {max_cant}", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=12), text_color=StyleConfig.accent_primary).pack(side="right", padx=10)
                entradas_dev[id_prod] = (entrada, max_cant)
                
            entrada.pack(side="right", padx=10)
            
        conexion.close()
            
        def confirmar_devolucion():
            lista_devolucion = []
            for id_p, (entrada, m_cant) in entradas_dev.items():
                try:
                    cant_ingr = int(entrada.get())
                    if cant_ingr > m_cant:
                        messagebox.showwarning("Inválido", f"Límite superado. Máximo para ID {id_p} es {m_cant}.", parent=ventana_dev)
                        return
                    if cant_ingr > 0:
                        lista_devolucion.append((id_p, cant_ingr))
                except ValueError:
                    pass
            
            if not lista_devolucion:
                messagebox.showinfo("Operación Nula", "No hay valores de reintegro asignados a la memoria.", parent=ventana_dev)
                return
                
            exito, dt = self.db.procesar_devolucion(id_venta, lista_devolucion)
            if exito:
                messagebox.showinfo("Reintegro Completo", f"FONDOS RETIRADOS: ${dt:.2f}", parent=ventana_dev)
                ventana_dev.destroy()
            else:
                messagebox.showerror("Error Crítico", f"Bloqueo en la Base de Datos:\n{dt}", parent=ventana_dev)
        
        ctk.CTkButton(ventana_dev, text="CONFIRMAR REVERSIÓN", fg_color=StyleConfig.accent_danger, hover_color="#881337", font=ctk.CTkFont(family=StyleConfig.font_button[0], weight="bold"), height=45, command=confirmar_devolucion).pack(pady=20, padx=20, fill="x")

    def exportar_ventas_csv(self):
        ventas = self.db.obtener_todas_las_ventas()
        if not ventas:
            messagebox.showwarning("Vacío", "No hay registros disponibles para dumpear.")
            return
        
        archivo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not archivo: return
        
        try:
            with open(archivo, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID Venta", "Fecha", "Cédula Cliente", "Nombre Cliente", "Método Pago", "Total Venta"])
                for v in ventas:
                    writer.writerow([v['id'], v['fecha'], v['id_cliente'], v['nombre_cliente'], v['metodo_pago'], v['total']])
            messagebox.showinfo("Éxito", f"Datos archivados localmente en:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Fallo de Extracción", f"Error I/O: {e}")

    def generar_cierre_caja_gui(self):
        tz_vzla = pytz.timezone('America/Caracas')
        fecha_cierre = datetime.now(tz_vzla).strftime('%Y-%m-%d')
        fecha_cierre_fmt = datetime.now(tz_vzla).strftime('%d-%m-%Y')
        reporte = self.db.obtener_reporte_cierre(fecha_cierre)

        ventana_cierre = ctk.CTkToplevel(self.app)
        ventana_cierre.title(f"Informe Operativo X/Z - {fecha_cierre_fmt}")
        ventana_cierre.geometry("450x750")
        ventana_cierre.configure(fg_color="#141416")
        ventana_cierre.attributes('-topmost', True)

        ctk.CTkLabel(ventana_cierre, text="MÉTRICAS DEL CICLO ACTIVO", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=18, weight="bold")).pack(pady=20)

        # Mostrar métricas
        frame_metrics = ctk.CTkFrame(ventana_cierre, fg_color=StyleConfig.bg_surface, corner_radius=StyleConfig.corner_radius_small)
        frame_metrics.pack(side="top", fill="both", expand=True, padx=20, pady=10)

        fn_label = ctk.CTkFont(family=StyleConfig.font_data[0], size=13)
        fn_val = ctk.CTkFont(family=StyleConfig.font_data[0], size=14, weight="bold")

        ctk.CTkLabel(frame_metrics, text="VÓLUMEN BASE (BRUTO):", font=fn_label, text_color=StyleConfig.text_muted).grid(row=0, column=0, sticky="w", padx=20, pady=15)
        ctk.CTkLabel(frame_metrics, text=f"${reporte['ingreso_bruto_sin_iva']:.2f}", font=fn_val).grid(row=0, column=1, sticky="e", padx=20, pady=15)

        ctk.CTkLabel(frame_metrics, text="CAPTACIÓN FISCAL (IVA):", font=fn_label, text_color=StyleConfig.text_muted).grid(row=1, column=0, sticky="w", padx=20, pady=15)
        ctk.CTkLabel(frame_metrics, text=f"${reporte['iva_recaudado']:.2f}", font=fn_val).grid(row=1, column=1, sticky="e", padx=20, pady=15)

        ctk.CTkLabel(frame_metrics, text="IMPACTO INVENTARIO (COGS):", font=fn_label, text_color=StyleConfig.text_muted).grid(row=2, column=0, sticky="w", padx=20, pady=15)
        ctk.CTkLabel(frame_metrics, text=f"${reporte['cogs']:.2f}", font=fn_val, text_color=StyleConfig.accent_danger).grid(row=2, column=1, sticky="e", padx=20, pady=15)

        ctk.CTkLabel(frame_metrics, text="DÉFICIT POR REINTEGRO:", font=fn_label, text_color=StyleConfig.text_muted).grid(row=3, column=0, sticky="w", padx=20, pady=15)
        ctk.CTkLabel(frame_metrics, text=f"${reporte['total_devoluciones']:.2f}", font=fn_val, text_color=StyleConfig.accent_primary).grid(row=3, column=1, sticky="e", padx=20, pady=15)

        ctk.CTkLabel(frame_metrics, text="CIRCULANTE EN EFECTIVO:", font=fn_label, text_color=StyleConfig.text_muted).grid(row=4, column=0, sticky="w", padx=20, pady=15)
        ctk.CTkLabel(frame_metrics, text=f"${reporte['efectivo_real_en_caja']:.2f}", font=fn_val, text_color=StyleConfig.accent_success).grid(row=4, column=1, sticky="e", padx=20, pady=15)

        separador = ctk.CTkFrame(frame_metrics, height=1, fg_color=StyleConfig.border_subtle)
        separador.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_metrics, text="--- TOTALES POR MONEDA ---", font=fn_label, text_color=StyleConfig.text_muted).grid(row=6, column=0, columnspan=2, pady=(10, 5))
        
        divisas = reporte['totales_por_metodo'].get("Divisas (USD)", 0.0)
        bolivares = reporte['totales_por_metodo'].get("Bolívares (VES)", 0.0)
        
        ctk.CTkLabel(frame_metrics, text="DIVISAS (USD):", font=fn_label, text_color=StyleConfig.text_main).grid(row=7, column=0, sticky="w", padx=20, pady=5)
        ctk.CTkLabel(frame_metrics, text=f"${divisas:.2f}", font=fn_val, text_color=StyleConfig.accent_success).grid(row=7, column=1, sticky="e", padx=20, pady=5)
        
        ctk.CTkLabel(frame_metrics, text="BOLÍVARES (VES):", font=fn_label, text_color=StyleConfig.text_main).grid(row=8, column=0, sticky="w", padx=20, pady=5)
        ctk.CTkLabel(frame_metrics, text=f"${bolivares:.2f}", font=fn_val, text_color=StyleConfig.accent_success).grid(row=8, column=1, sticky="e", padx=20, pady=5)

        separador2 = ctk.CTkFrame(frame_metrics, height=1, fg_color=StyleConfig.border_subtle)
        separador2.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_metrics, text="UTILIDAD ESTIMADA:", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=14, weight="bold")).grid(row=10, column=0, sticky="w", padx=20, pady=20)
        ctk.CTkLabel(frame_metrics, text=f"${reporte['ganancia_neta_estimada']:.2f}", font=ctk.CTkFont(family=StyleConfig.font_data_large[0], size=22, weight="bold"), text_color=StyleConfig.accent_success).grid(row=10, column=1, sticky="e", padx=20, pady=20)

        def exportar_cierre():
            try:
                pdf_path = generar_pdf_cierre_caja(reporte, fecha_cierre)
                messagebox.showinfo("Trámite Exitoso", f"REPORTE REGISTRADO EN RED LOCAL:\n{pdf_path}", parent=ventana_cierre)
            except Exception as e:
                messagebox.showerror("Error de Interfaz", f"Compilación de archivo PDF fallida:\n{e}", parent=ventana_cierre)
                
        # --- ACCIONES FINALES ---
        btn_pdf = ctk.CTkButton(
            ventana_cierre, 
            text="GENERAR PDF", 
            command=exportar_cierre, 
            fg_color=StyleConfig.accent_danger, 
            hover_color="#991B1B", 
            text_color="#FFFFFF", 
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=14, weight="bold"), 
            height=50,
            corner_radius=15
        )
        btn_pdf.pack(fill="x", padx=40, pady=(20, 10))

        btn_descartar = ctk.CTkButton(
            ventana_cierre, 
            text="CERRAR VENTANA", 
            command=ventana_cierre.destroy, 
            fg_color="transparent", 
            border_color=StyleConfig.border_subtle, 
            border_width=1,
            text_color=StyleConfig.text_muted,
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=12),
            height=35
        )
        btn_descartar.pack(pady=(0, 20))

        ventana_cierre.update_idletasks()
