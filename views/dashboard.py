import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pytz
import os
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Inventario import Inventario, Producto
from generador_pdf import generar_pdf_factura, generar_pdf_cierre_caja
from style_config import StyleConfig

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, db, app):
        super().__init__(parent, fg_color='transparent')
        self.pack(fill='both', expand=True, padx=StyleConfig.padding_global, pady=StyleConfig.padding_global)
        self.db = db
        self.app = app
        
        # Encabezado de Acciones y Estado
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Acciones Rápidas (Izquierda)
        qa_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        qa_frame.pack(side="left")
        
        btn_style = {
            "font": ctk.CTkFont(family=StyleConfig.font_button[0], size=12, weight="bold"),
            "height": 35,
            "corner_radius": StyleConfig.corner_radius_small,
            "border_width": 1,
            "border_color": StyleConfig.border_subtle
        }
        
        ctk.CTkButton(qa_frame, text="NUEVA VENTA", fg_color=StyleConfig.bg_surface, hover_color=StyleConfig.border_subtle, 
                      text_color=StyleConfig.accent_primary, command=self.app.mostrar_pos, **btn_style).pack(side="left", padx=(0, 10))
        ctk.CTkButton(qa_frame, text="VER INVENTARIO", fg_color=StyleConfig.bg_surface, hover_color=StyleConfig.border_subtle, 
                      text_color=StyleConfig.text_main, command=self.app.mostrar_inventario, **btn_style).pack(side="left", padx=10)
        ctk.CTkButton(qa_frame, text="VER VENTAS", fg_color=StyleConfig.bg_surface, hover_color=StyleConfig.border_subtle, 
                      text_color=StyleConfig.text_main, command=self.app.mostrar_ventas, **btn_style).pack(side="left", padx=10)

        # Respaldo (Derecha)
        backup_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        backup_frame.pack(side="right")
        self.lbl_backup = ctk.CTkLabel(backup_frame, text="VERIFICANDO RESPALDO...", font=ctk.CTkFont(family=StyleConfig.font_data[0], size=10), text_color=StyleConfig.text_muted)
        self.lbl_backup.pack(side="left", padx=10)
        ctk.CTkButton(backup_frame, text="CREAR RESPALDO", fg_color=StyleConfig.bg_surface, hover_color=StyleConfig.border_subtle, 
                      text_color=StyleConfig.text_main, command=self.ejecutar_respaldo_gui, **btn_style).pack(side="left")
        
        self.actualizar_estado_backup()

        # Canvas Scrollable principal
        scroll_dash = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_dash.pack(fill="both", expand=True)

        # --- CONTENEDOR DE TARJETAS (VAULT CARDS) ---
        cards_frame = ctk.CTkFrame(scroll_dash, fg_color="transparent")
        cards_frame.pack(fill="x", pady=10)

        total_prods = self.db.obtener_total_productos()
        total_clientes = self.db.obtener_total_clientes()
        valor_almacen = self.db.obtener_valor_total_almacen_costo()

        card_style = {
            "fg_color": StyleConfig.bg_surface,
            "border_color": StyleConfig.border_subtle,
            "border_width": StyleConfig.border_width,
            "corner_radius": StyleConfig.corner_radius_large,
            "height": 130
        }

        # Card: Valor Total (Pieza Central, gigante)
        card_valor = ctk.CTkFrame(cards_frame, **card_style)
        card_valor.pack(side="left", padx=(0, 10), fill="x", expand=True)
        card_valor.pack_propagate(False)
        ctk.CTkLabel(card_valor, text="VALOR TOTAL EN ALMACÉN", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=12, weight="bold"), text_color=StyleConfig.text_muted).pack(anchor="w", padx=20, pady=(20, 0))
        self.label_stats_valor = ctk.CTkLabel(card_valor, text=f"${valor_almacen:,.2f}", font=ctk.CTkFont(family=StyleConfig.font_data_large[0], size=40, weight="bold"), text_color=StyleConfig.accent_success)
        self.label_stats_valor.pack(anchor="w", padx=20, pady=5)

        # Card: Total Stock
        card_prods = ctk.CTkFrame(cards_frame, **card_style)
        card_prods.pack(side="left", padx=10, fill="x", expand=True)
        card_prods.pack_propagate(False)
        ctk.CTkLabel(card_prods, text="ITEMS EN STOCK", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=12, weight="bold"), text_color=StyleConfig.text_muted).pack(anchor="w", padx=20, pady=(20, 0))
        self.label_stats_prods = ctk.CTkLabel(card_prods, text=str(total_prods), font=ctk.CTkFont(family=StyleConfig.font_data_large[0], size=32, weight="bold"), text_color=StyleConfig.text_main)
        self.label_stats_prods.pack(anchor="w", padx=20, pady=5)

        # Card: Total Clientes
        card_clientes = ctk.CTkFrame(cards_frame, **card_style)
        card_clientes.pack(side="left", padx=(10, 0), fill="x", expand=True)
        card_clientes.pack_propagate(False)
        ctk.CTkLabel(card_clientes, text="CLIENTES REGISTRADOS", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=12, weight="bold"), text_color=StyleConfig.text_muted).pack(anchor="w", padx=20, pady=(20, 0))
        self.label_stats_clientes = ctk.CTkLabel(card_clientes, text=str(total_clientes), font=ctk.CTkFont(family=StyleConfig.font_data_large[0], size=32, weight="bold"), text_color=StyleConfig.text_main)
        self.label_stats_clientes.pack(anchor="w", padx=20, pady=5)

        # --- SECCIÓN DE GRÁFICOS (INDUSTRIAL GRAPHS) ---
        graficas_frame = ctk.CTkFrame(scroll_dash, fg_color="transparent", height=300)
        graficas_frame.pack(fill="both", expand=True, pady=15)

        # Configuración común para matplotlib para estilo The Vault
        plt_bg = StyleConfig.bg_surface
        plt_fg = StyleConfig.text_muted

        # Gráfico: Ventas 7 Días
        grafica_left = ctk.CTkFrame(graficas_frame, **card_style)
        grafica_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        fig_line = Figure(figsize=(5, 3), dpi=100, facecolor=plt_bg)
        ax_line = fig_line.add_subplot(111)
        ax_line.set_facecolor(plt_bg)
        ax_line.tick_params(colors=plt_fg, labelsize=8)
        # Quitar bordes invasivos (manteniendo solo bottom e izq)
        ax_line.spines['top'].set_visible(False)
        ax_line.spines['right'].set_visible(False)
        ax_line.spines['bottom'].set_color(StyleConfig.border_subtle)
        ax_line.spines['left'].set_color(StyleConfig.border_subtle)
            
        ventas_7_dias = self.db.obtener_ventas_ultimos_7_dias()
        fechas = [v[0][8:10] + "/" + v[0][5:7] for v in ventas_7_dias] 
        montos = [v[1] for v in ventas_7_dias]
        
        ax_line.plot(fechas, montos, color=StyleConfig.accent_primary, marker="o", markersize=6, linewidth=2, solid_capstyle='round')
        ax_line.set_title("FLUJO DE VENTAS (Últimos 7 dias)", color=StyleConfig.text_main, pad=20, fontdict={'fontname': 'Montserrat', 'fontsize': 10, 'fontweight': 'bold'})
        fig_line.tight_layout(pad=2.0)
        
        canvas_line = FigureCanvasTkAgg(fig_line, master=grafica_left)
        canvas_line.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Gráfico: Top 5 Productos
        grafica_right = ctk.CTkFrame(graficas_frame, **card_style)
        grafica_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        fig_bar = Figure(figsize=(5, 3), dpi=100, facecolor=plt_bg)
        ax_bar = fig_bar.add_subplot(111)
        ax_bar.set_facecolor(plt_bg)
        ax_bar.tick_params(colors=plt_fg, labelsize=8)
        ax_bar.spines['top'].set_visible(False)
        ax_bar.spines['right'].set_visible(False)
        ax_bar.spines['bottom'].set_color(StyleConfig.border_subtle)
        ax_bar.spines['left'].set_color(StyleConfig.border_subtle)
            
        top_productos = self.db.obtener_top_productos_30_dias()
        nombres_top = [p[0][:12] for p in top_productos] # Cortar strings largos
        Cants_top = [p[1] for p in top_productos]
        
        ax_bar.bar(nombres_top, Cants_top, color=StyleConfig.border_subtle, edgecolor=StyleConfig.accent_success, linewidth=1.5)
        ax_bar.set_title("VOLUMEN DE VENTAS (Últimos 30 dias)", color=StyleConfig.text_main, pad=20, fontdict={'fontname': 'Montserrat', 'fontsize': 10, 'fontweight': 'bold'})
        fig_bar.tight_layout(pad=2.0)

        canvas_bar = FigureCanvasTkAgg(fig_bar, master=grafica_right)
        canvas_bar.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # --- ALERTAS INFERIORES ---
        lower_frame = ctk.CTkFrame(scroll_dash, fg_color="transparent")
        lower_frame.pack(fill="x", pady=15)

        # Alertas de Stock
        alertas_container = ctk.CTkFrame(lower_frame, **card_style)
        alertas_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(alertas_container, text="[!] ALERTA DE STOCK BAJO: MENOS DE 5 UNIDADES", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=12, weight="bold"), text_color=StyleConfig.accent_danger).pack(anchor="w", padx=20, pady=(15, 5))
        self.alertas_frame = ctk.CTkScrollableFrame(alertas_container, fg_color="transparent", height=120)
        self.alertas_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Productos Muertos
        muertos_container = ctk.CTkFrame(lower_frame, **card_style)
        muertos_container.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(muertos_container, text="[-] ESTANCAMIENTO: PRODUCTOS SIN MOVIMIENTO (Últimos 30 dias)", font=ctk.CTkFont(family=StyleConfig.font_title[0], size=12, weight="bold"), text_color=StyleConfig.text_muted).pack(anchor="w", padx=20, pady=(15, 5))
        self.muertos_frame = ctk.CTkScrollableFrame(muertos_container, fg_color="transparent", height=120)
        self.muertos_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.actualizar_alertas_dashboard()

    def actualizar_estado_backup(self):
        try:
            if not os.path.exists("Backups"):
                self.lbl_backup.configure(text="SIN RESPALDOS", text_color=StyleConfig.accent_danger)
                return
            archivos = [os.path.join("Backups", f) for f in os.listdir("Backups") if f.endswith(".db")]
            if not archivos:
                self.lbl_backup.configure(text="SIN RESPALDOS", text_color=StyleConfig.accent_danger)
                return
            archivo_mas_reciente = max(archivos, key=os.path.getctime)
            tiempo = os.path.getctime(archivo_mas_reciente)
            diferencia = datetime.now() - datetime.fromtimestamp(tiempo)
            
            horas = int(diferencia.total_seconds() // 3600)
            if horas < 1:
                msj = "RESPALDO: < 1H (SEGURO)"
                color = StyleConfig.accent_success
            else:
                msj = f"RESPALDO: HACE {horas}H"
                color = StyleConfig.accent_primary if horas < 24 else StyleConfig.accent_danger
                
            self.lbl_backup.configure(text=msj, text_color=color)
        except Exception as e:
            self.lbl_backup.configure(text=f"ERROR DE I/O: RESPALDO", text_color=StyleConfig.accent_danger)

    def ejecutar_respaldo_gui(self):
        exito, msj = self.db.respaldar_base_datos()
        if exito:
            messagebox.showinfo("Respaldo Exitoso", f"Copia creada en:\n{msj}")
            self.actualizar_estado_backup()
        else:
            messagebox.showerror("Error", f"Fallo al respaldar:\n{msj}")

    def refrescar_dashboard(self):
        if hasattr(self.app, 'mostrar_dashboard'):
            self.app.mostrar_dashboard()

    def actualizar_alertas_dashboard(self):
        # Limpiar Frames
        for widget in self.alertas_frame.winfo_children(): widget.destroy()
        for widget in self.muertos_frame.winfo_children(): widget.destroy()

        # Configuraciones de fuente para las filas de las listas
        font_data = ctk.CTkFont(family=StyleConfig.font_data[0], size=12)

        try:
            productos_bajos = self.db.reporte_stock_bajo(5)
            if not productos_bajos:
                ctk.CTkLabel(self.alertas_frame, text="No hay productos con bajo Stock.", text_color=StyleConfig.text_muted, font=font_data).pack(pady=10, anchor="w")
            else:
                for p in productos_bajos:
                    # p = id, nombre, categoria, precio, costo, cantidad
                    txt = f"ID:{p[0]} | {str(p[1]).upper():<20} | QTY: {p[5]}"
                    ctk.CTkLabel(self.alertas_frame, text=txt, text_color=StyleConfig.text_main, font=font_data).pack(anchor="w", pady=2)

            p_muertos = self.db.obtener_productos_muertos_30_dias()
            if not p_muertos:
                ctk.CTkLabel(self.muertos_frame, text="Todos los productos tienen movimiento.", text_color=StyleConfig.text_muted, font=font_data).pack(pady=10, anchor="w")
            else:
                for pm in p_muertos:  # pm: id, nombre, cantidad
                    txt = f"ID:{pm[0]} | {str(pm[1]).upper():<20} | QTY: {pm[2]}"
                    ctk.CTkLabel(self.muertos_frame, text=txt, text_color=StyleConfig.text_muted, font=font_data).pack(anchor="w", pady=2)
        except Exception as e:
            print(f"Error al actualizar alertas: {e}")

    
