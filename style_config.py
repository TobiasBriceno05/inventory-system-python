# Configuración de Diseño: The Vault
# Contiene constantes globales de colores, fuentes y radios para asegurar consistencia "Pixel-Perfect".

class StyleConfig:
    # --- PALETA DE COLORES (Industrial Dark - Ledger Vibe) ---
    bg_base = "#0A0A0B"          # Negro abisal, fondo rey
    bg_surface = "#141416"       # Gris profundo para tarjetas y paneles
    border_subtle = "#232326"    # Bordes sutiles
    
    accent_primary = "#FACC15"   # Amarillo eléctrico (Acción / Selección)
    accent_success = "#00913F"   # Verde glaciar (Éxito / Dinero)
    accent_danger = "#F43F5E"    # Rojo rosáceo (Errores / Eliminar)
    
    text_main = "#FFFFFF"        # Texto principal luminoso
    text_muted = "#8A8A93"       # Texto secundario/técnico

    # --- GEOMETRÍA Y COMPOSICIÓN ---
    corner_radius_large = 20     # Tarjetas principales
    corner_radius_small = 8      # Botones, inputs
    padding_global = 30
    border_width = 1

    # --- TIPOGRAFÍA (Tuplas para CTkFont directo) ---
    # Familia, Tamaño, Peso
    font_title = ("Montserrat", 24, "bold")
    font_subtitle = ("Montserrat", 18, "bold")
    font_button = ("Montserrat", 14, "bold")
    
    # JetBrains Mono ideal para data, números, IDs
    font_data_large = ("JetBrains Mono", 32, "bold")
    font_data = ("JetBrains Mono", 14, "normal")
    font_data_bold = ("JetBrains Mono", 14, "bold")
    
    # Fallbacks: Las fuentes en Tkinter caerán a una fuente predeterminada (Arial/TkDefault) 
    # si el SO no las tiene instaladas. Recomiendo instalarlas en Windows para la experiencia ideal.
