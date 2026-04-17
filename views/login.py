import customtkinter as ctk
from tkinter import messagebox
from style_config import StyleConfig

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent_app, db):
        super().__init__()
        self.parent_app = parent_app
        self.db = db
        
        self.title("OmniStock - Gateway")
        self.geometry("450x550")
        self.resizable(False, False)
        
        # Fondo Vault
        self.configure(fg_color=StyleConfig.bg_base)
        
        # Ocultar la ventana principal hasta el login exitoso
        self.parent_app.withdraw()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Contenedor centralizado
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # El "Vault" (Frame central)
        self.frame = ctk.CTkFrame(
            self, 
            fg_color=StyleConfig.bg_surface,
            border_color=StyleConfig.border_subtle,
            border_width=StyleConfig.border_width,
            corner_radius=StyleConfig.corner_radius_large
        )
        self.frame.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        
        # Alinear contenido en el Vault
        self.frame.grid_columnconfigure(0, weight=1)

        # Header Vault
        self.logo = ctk.CTkLabel(
            self.frame, 
            text="OMNISTOCK //", 
            font=ctk.CTkFont(family=StyleConfig.font_title[0], size=StyleConfig.font_title[1], weight=StyleConfig.font_title[2]),
            text_color=StyleConfig.text_main
        )
        self.logo.grid(row=0, column=0, pady=(60, 10))
        
        self.sub_logo = ctk.CTkLabel(
            self.frame, 
            text="SECURE ACCESS TERMINAL", 
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=10),
            text_color="#0e5496"
        )
        self.sub_logo.grid(row=1, column=0, pady=(0, 40))

        # Inputs Industriales
        self.txt_usuario = ctk.CTkEntry(
            self.frame, 
            placeholder_text="ID USUARIO", 
            width=280, 
            height=45,
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=StyleConfig.font_data[1]),
            fg_color=StyleConfig.bg_base,
            border_color=StyleConfig.border_subtle,
            border_width=1,
            corner_radius=StyleConfig.corner_radius_small,
            text_color=StyleConfig.text_main,
            placeholder_text_color=StyleConfig.text_muted
        )
        self.txt_usuario.grid(row=2, column=0, pady=10)

        self.txt_password = ctk.CTkEntry(
            self.frame, 
            placeholder_text="CLAVE DE ACCESO", 
            show="*", 
            width=280, 
            height=45,
            font=ctk.CTkFont(family=StyleConfig.font_data[0], size=StyleConfig.font_data[1]),
            fg_color=StyleConfig.bg_base,
            border_color=StyleConfig.border_subtle,
            border_width=1,
            corner_radius=StyleConfig.corner_radius_small,
            text_color=StyleConfig.text_main,
            placeholder_text_color=StyleConfig.text_muted
        )
        self.txt_password.grid(row=3, column=0, pady=10)
        self.txt_password.bind("<Return>", lambda event: self.iniciar_sesion())

        # Botón Brutalista
        self.btn_login = ctk.CTkButton(
            self.frame, 
            text="Iniciar Sesión", 
            width=280, 
            height=50,
            font=ctk.CTkFont(family=StyleConfig.font_button[0], size=16, weight="bold"),
            fg_color="#FACC15",
            hover_color="#b59619",
            text_color="#000000",   
            corner_radius=StyleConfig.corner_radius_small,
            command=self.iniciar_sesion
        )
        self.btn_login.grid(row=4, column=0, pady=(30, 20))

    def iniciar_sesion(self):
        usuario = self.txt_usuario.get().strip()
        password = self.txt_password.get().strip()
        
        if not usuario or not password:
            messagebox.showwarning("Faltan Datos", "Debe ingresar ID USUARIO y CLAVE DE ACCESO.", parent=self)
            return

        resultado = self.db.verificar_login(usuario, password)
        if resultado is not None:
            # resultado es (id, usuario)
            self.parent_app.usuario_actual = resultado
            self.parent_app.deiconify() # Revelar la app principal
            self.destroy()
        else:
            messagebox.showerror("Error", "ID USUARIO o CLAVE incorrectos. Acceso denegado.", parent=self)

    def _on_closing(self):
        self.parent_app.destroy()
