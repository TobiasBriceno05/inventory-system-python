import os
from datetime import datetime
import pytz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

MESES_ESP = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def generar_pdf_factura(datos_venta, cliente_info):
    """
    Genera un archivo PDF con el detalle de la venta.
    Guarda el PDF organizándolo en carpetas: YYYY/Mes/DD/factura_{id_venta}.pdf
    """
    
    # Crear estructura de carpetas
    tz_vzla = pytz.timezone('America/Caracas')
    hoy = datetime.now(tz_vzla)
    nombre_mes = MESES_ESP[hoy.month]
    ruta_carpeta = os.path.join("Registros Financieros", str(hoy.year), nombre_mes, f"{hoy.day:02d}")
    os.makedirs(ruta_carpeta, exist_ok=True)
    
    id_venta = datos_venta.get("id_venta", "N-A")
    nombre_archivo = os.path.join(ruta_carpeta, f"factura_{id_venta}.pdf")
    
    documento = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    estilos = getSampleStyleSheet()
    elementos = []
    
    # Encabezado
    titulo = Paragraph("<b>OmniStock - Factura de Venta</b>", estilos['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))
    
    fecha_venta = datos_venta.get("fecha", hoy.strftime('%Y-%m-%d %H:%M:%S'))
    if len(fecha_venta) >= 16:
        partes = fecha_venta.split()
        fecha_str = partes[0].split('-')
        if len(fecha_str) == 3:
            hora_str = ":".join(partes[1].split(':')[:2])
            fecha_venta = f"{fecha_str[2]}-{fecha_str[1]}-{fecha_str[0]} {hora_str}"

    info_venta = f"<b>Fecha:</b> {fecha_venta}<br/><b>No. Factura:</b> {id_venta}"
    elementos.append(Paragraph(info_venta, estilos['Normal']))
    elementos.append(Spacer(1, 12))
    
    # Información del cliente
    nombre_cliente = cliente_info[1] if cliente_info else "Consumidor Final"
    cedula_cliente = cliente_info[0] if cliente_info else "N/A"
    info_cli = f"<b>Cliente:</b> {nombre_cliente}<br/><b>C.I / RIF:</b> {cedula_cliente}"
    elementos.append(Paragraph(info_cli, estilos['Normal']))
    elementos.append(Spacer(1, 20))
    
    # Tabla de Productos
    datos_tabla = [["Producto", "CANT", "Precio Unit.", "Subtotal"]]
    # datos_venta["productos"] viene como una lista según se preparó para el PDF.
    # En el POS el carrito tiene diccionarios: {'id', 'nombre', 'precio', 'cantidad'}
    # Como registrar_venta no tiene los nombres para retornar, pasaremos los del carrito.
    
    for p in datos_venta.get("carrito_detalle", []):
        subt_prod = p['cantidad'] * p['precio']
        datos_tabla.append([
            p['nombre'], 
            str(p['cantidad']), 
            f"${p['precio']:.2f}", 
            f"${subt_prod:.2f}"
        ])
    
    tabla = Table(datos_tabla, colWidths=[250, 50, 100, 100])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 20))
    
    # Totales
    subtotal = datos_venta.get("subtotal", 0.0)
    iva = datos_venta.get("iva", 0.0)
    total = datos_venta.get("total", 0.0)
    
    totales_texto = f"""
    <b>Base Imponible:</b> ${subtotal:.2f}<br/>
    <b>IVA Recargado:</b> ${iva:.2f}<br/>
    <b>TOTAL A PAGAR:</b> ${total:.2f}
    """
    estilo_totales = estilos['Normal']
    estilo_totales.alignment = 2 # Right
    elementos.append(Paragraph(totales_texto, estilo_totales))
    
    documento.build(elementos)
    return nombre_archivo

def generar_pdf_cierre_caja(reporte_datos, fecha_cierre):
    """
    Genera el PDF del Cierre de Caja PRO
    reporte_datos es el diccionario generado por obtener_reporte_cierre
    """
    tz_vzla = pytz.timezone('America/Caracas')
    hoy = datetime.now(tz_vzla)
    nombre_mes = MESES_ESP[hoy.month]
    ruta_carpeta = os.path.join("Registros Financieros", str(hoy.year), nombre_mes, f"{hoy.day:02d}")
    os.makedirs(ruta_carpeta, exist_ok=True)
    
    nombre_archivo = os.path.join(ruta_carpeta, f"Cierre_Caja_{hoy.strftime('%Y%m%d_%H%M')}.pdf")
    documento = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    estilos = getSampleStyleSheet()
    elementos = []
    
    # Titulo
    titulo = Paragraph("<b>OmniStock - Cierre de Caja Diario (PRO)</b>", estilos['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))
    
    elementos.append(Paragraph(f"<b>Fecha Auditada:</b> {fecha_cierre}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Fecha de Emisión:</b> {hoy.strftime('%d-%m-%Y %H:%M')}", estilos['Normal']))
    elementos.append(Spacer(1, 20))
    
    # MÉTRICAS GENERALES
    elementos.append(Paragraph("<b>Indicadores Financieros Generales</b>", estilos['Heading2']))
    
    data_resumen = [
        ["Concepto", "Monto"],
        ["Ingreso Bruto (Sin IVA)", f"${reporte_datos['ingreso_bruto_sin_iva']:.2f}"],
        ["IVA Recaudado", f"${reporte_datos['iva_recaudado']:.2f}"],
        ["Costo Mercancía (COGS)", f"${reporte_datos['cogs']:.2f}"],
        ["Total Devoluciones", f"${reporte_datos['total_devoluciones']:.2f}"],
        ["Ganancia Neta Estimada", f"${reporte_datos['ganancia_neta_estimada']:.2f}"]
    ]
    t_resumen = Table(data_resumen, colWidths=[300, 150])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.red), # COGS en rojo
        ('TEXTCOLOR', (1, 5), (1, 5), colors.green), # Ganancia en verde
    ]))
    elementos.append(t_resumen)
    elementos.append(Spacer(1, 20))
    
    # INGRESOS POR METODO DE PAGO
    elementos.append(Paragraph("<b>Totales por Método de Pago</b>", estilos['Heading2']))
    if reporte_datos.get("totales_por_metodo"):
        data_metodos = [["Método de Pago", "Total Ingresado"]]
        for metodo, total_m in reporte_datos["totales_por_metodo"].items():
            data_metodos.append([str(metodo), f"${total_m:.2f}"])
            
        t_metodos = Table(data_metodos, colWidths=[200, 150])
        t_metodos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elementos.append(t_metodos)
    else:
        elementos.append(Paragraph("No hay ingresos por métodos de pago.", estilos['Normal']))
    
    elementos.append(Spacer(1, 20))
    
    # LISTADO DE VENTAS DEL DIA
    elementos.append(Paragraph("<b>Desglose de Ventas de la Jornada</b>", estilos['Heading2']))
    if reporte_datos.get("ventas_dia"):
        data_ventas = [["ID", "Hora/Fecha", "C.I Cliente", "Método", "Total"]]
        for v in reporte_datos.get("ventas_dia", []):
            data_ventas.append([
                str(v['id_venta']),
                v['fecha'],
                v['id_cliente'],
                v['metodo_pago'],
                f"${v['total']:.2f}"
            ])
            
        t_ventas = Table(data_ventas, colWidths=[40, 150, 100, 100, 80])
        t_ventas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        elementos.append(t_ventas)
    else:
        elementos.append(Paragraph("No hubo ventas registradas este día.", estilos['Normal']))
        
    documento.build(elementos)
    return nombre_archivo