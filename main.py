import customtkinter as ctk
from datetime import datetime
import pytz
from Inventario import Inventario
from views.login import LoginWindow
from views.dashboard import DashboardView
from views.clientes import ClientesView
from views.inventario import InventarioView
from views.ventas import VentasView
from views.pos import POSView
from tkinter import ttk
from style_config import StyleConfig

class AppOmniStock(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. CONFIGURACIÓN PRINCIPAL ---
        self.title("OmniStock CRM & POS - Nivel Empresarial")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # Fondo Global Vault
        self.configure(fg_color=StyleConfig.bg_base)
        ctk.set_appearance_mode("dark")

        # Inicializamos el backend
        self.db = Inventario()
        self.usuario_actual = None # Tupla (id, usuario)

        # Configurar el grid principal (1 fila, 2 columnas)
        self.grid_rowconfigure(1, weight=1)  # Fila 1 para contenido principal
        self.grid_columnconfigure(1, weight=1) # Columna 1 para main_frame

        # --- HEADER (Reloj minimalista) ---
        self.header_frame = ctk.CTkFrame(self, height=50, fg_color=StyleConfig.bg_base, corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_propagate(False)

        self.lbl_reloj = ctk.CTkLabel(
            self.header_frame, 
            text="UTC-4 / 00:00", 
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=14, weight="bold"),
            text_color=StyleConfig.text_muted
        )
        self.lbl_reloj.grid(row=0, column=0, sticky="e", padx=30, pady=15)
        
        self.lbl_saludo_top = ctk.CTkLabel(
            self.header_frame, 
            text="DESCONECTADO", 
            font=ctk.CTkFont(family=StyleConfig.font_data_bold[0], size=14),
            text_color=StyleConfig.text_muted
        )
        self.lbl_saludo_top.grid(row=0, column=0, sticky="w", padx=30, pady=15)

        # --- 2. BARRA LATERAL (SIDEBAR ESTÁTICA THE VAULT) ---
        self.sidebar_frame = ctk.CTkFrame(
            self, 
            width=220, 
            corner_radius=0, 
            fg_color=StyleConfig.bg_surface,
            border_width=1,
            border_color=StyleConfig.border_subtle
        )
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(30, 0), pady=(0, 30))
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="OMNISTOCK", 
            font=ctk.CTkFont(family=StyleConfig.font_title[0], size=20, weight="bold"),
            text_color=StyleConfig.text_main
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        # Configuración de botones de navegación (Sin colores brillantes de relleno)
        btn_config = {
            "font": ctk.CTkFont(family=StyleConfig.font_button[0], size=13, weight="bold"),
            "fg_color": "transparent",
            "text_color": StyleConfig.text_muted,
            "hover_color": StyleConfig.border_subtle,
            "anchor": "w",
            "corner_radius": StyleConfig.corner_radius_small,
            "height": 45
        }

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text=" 📊 DASHBOARD", command=self.mostrar_dashboard, **btn_config)
        self.btn_dashboard.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.btn_pos = ctk.CTkButton(self.sidebar_frame, text=" 🛒 PUNTO VENTA", command=self.mostrar_pos, **btn_config)
        self.btn_pos.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.btn_clientes = ctk.CTkButton(self.sidebar_frame, text=" 👥 CLIENTES", command=self.mostrar_clientes, **btn_config)
        self.btn_clientes.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        self.btn_inventario = ctk.CTkButton(self.sidebar_frame, text=" 📦 INVENTARIO", command=self.mostrar_inventario, **btn_config)
        self.btn_inventario.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        self.btn_ventas = ctk.CTkButton(self.sidebar_frame, text=" 🧾 VENTAS", command=self.mostrar_ventas, **btn_config)
        self.btn_ventas.grid(row=5, column=0, padx=15, pady=5, sticky="ew")

        # Estado del sistema al fondo abajo
        self.lbl_estado = ctk.CTkLabel(
            self.sidebar_frame, 
            text="SYS: ONLINE", 
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=10),
            text_color="#0e5496"
        )
        self.lbl_estado.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        # --- 3. PANEL PRINCIPAL (MAIN FRAME) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=StyleConfig.corner_radius_large, fg_color=StyleConfig.bg_base)
        self.main_frame.grid(row=1, column=1, padx=(10, 30), pady=(0, 30), sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Estilos para tablas globales
        self.configurar_estilos_tablas()

        # Iniciar login
        self.after(100, self.iniciar_login)

    def iniciar_login(self):
        login = LoginWindow(self, self.db)
        login.focus_force() 
        self.wait_window(login)
        
        if self.usuario_actual:
            self.actualizar_reloj()
            self.mostrar_dashboard()
        else:
            self.destroy() 

    def actualizar_reloj(self):
        tz_vzla = pytz.timezone('America/Caracas')
        ahora = datetime.now(tz_vzla)
        hora_str = ahora.strftime("%H:%M")
        
        if hasattr(self, 'lbl_reloj'):
            self.lbl_reloj.configure(text=f"UTC-4 / {hora_str}")
            
        nombre_usr = self.usuario_actual[1].upper() if self.usuario_actual else "UNKNOWN"
        if hasattr(self, 'lbl_saludo_top'):
            self.lbl_saludo_top.configure(text=f"OPERADOR: {nombre_usr}", text_color=StyleConfig.text_main)
            
        self.after(1000, self.actualizar_reloj)
        
    def resaltar_boton_activo(self, boton_activo):
        botones = [self.btn_dashboard, self.btn_pos, self.btn_clientes, self.btn_inventario, self.btn_ventas]
        for b in botones:
            if b == boton_activo:
                b.configure(fg_color=StyleConfig.border_subtle, text_color=StyleConfig.accent_primary)
            else:
                b.configure(fg_color="transparent", text_color=StyleConfig.text_muted)

    def configurar_estilos_tablas(self):
        style = ttk.Style()
        style.theme_use("default")
        
        # Color de fondo principal y selección
        style.configure("Treeview", 
                        background=StyleConfig.bg_surface,
                        foreground=StyleConfig.text_main,
                        rowheight=35,
                        fieldbackground=StyleConfig.bg_base,
                        borderwidth=0,
                        font=(StyleConfig.font_data[0], 11))
                        
        # Remover bordes extraños de Tkinter
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        # Efecto de selección
        style.map('Treeview', 
                  background=[('selected', StyleConfig.border_subtle)],
                  foreground=[('selected', StyleConfig.accent_primary)])
                  
        # Cabeceras
        style.configure("Treeview.Heading",
                        background=StyleConfig.bg_base,
                        foreground=StyleConfig.text_muted,
                        font=(StyleConfig.font_title[0], 10, "bold"),
                        borderwidth=0,
                        relief="flat")
                        
        style.map("Treeview.Heading", background=[('active', StyleConfig.bg_surface)])

    def limpiar_panel(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def mostrar_dashboard(self):
        self.limpiar_panel()
        self.resaltar_boton_activo(self.btn_dashboard)
        DashboardView(self.main_frame, self.db, self)

    def mostrar_pos(self):
        self.limpiar_panel()
        self.resaltar_boton_activo(self.btn_pos)
        POSView(self.main_frame, self.db, self)

    def mostrar_clientes(self):
        self.limpiar_panel()
        self.resaltar_boton_activo(self.btn_clientes)
        ClientesView(self.main_frame, self.db, self)

    def mostrar_inventario(self):
        self.limpiar_panel()
        self.resaltar_boton_activo(self.btn_inventario)
        InventarioView(self.main_frame, self.db, self)
        
    def mostrar_ventas(self):
        self.limpiar_panel()
        self.resaltar_boton_activo(self.btn_ventas)
        VentasView(self.main_frame, self.db, self)

if __name__ == "__main__":
    app = AppOmniStock()
    app.mainloop()
