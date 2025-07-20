# app.py - Aplicación Streamlit para extraer datos de PDFs de caja

import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from datetime import datetime
import base64

# Configuración de la página
st.set_page_config(
    page_title="Extractor de Datos - Informes de Caja",
    page_icon="💰",
    layout="wide"
)

# CSS personalizado para mejor apariencia
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Título y descripción
st.title("💰 Extractor de Datos - Informes de Caja")
st.markdown("### Sube tus archivos PDF de informes diarios para extraer los datos automáticamente")

# Funciones de extracción (las mismas del script anterior)
def limpiar_valor_monetario(valor):
    """Limpia valores monetarios removiendo $ y comas"""
    if valor:
        return valor.replace('$', '').replace(',', '').strip()
    return '0'

def extraer_datos_pdf(contenido_texto):
    """Extrae los campos específicos del contenido del PDF"""
    
    datos = {
        'Apertura': '',
        'Cierre': '',
        'V_Bruta': 0,
        'Total': 0,
        'Efectivo': 0,
        'Datafono': 0,
        'Total_Egresos': 0,
        'Diferencia': 0
    }
    
    try:
        # Extraer Apertura (A:)
        patron_apertura = r'A:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+[AP]M)'
        match_apertura = re.search(patron_apertura, contenido_texto)
        if match_apertura:
            datos['Apertura'] = match_apertura.group(1)
        
        # Extraer Cierre (C:)
        patron_cierre = r'C:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+[AP]M)'
        match_cierre = re.search(patron_cierre, contenido_texto)
        if match_cierre:
            datos['Cierre'] = match_cierre.group(1)
        
        # Extraer V. Bruta y Total
        patron_seccion_facturas = r'DATOS DE FACTURAS[\s\S]*?V\.\s*Bruta\s*:\s*\$?([\d,]+)[\s\S]*?Total\s*:\s*\$?([\d,]+)'
        match_facturas = re.search(patron_seccion_facturas, contenido_texto)
        if match_facturas:
            datos['V_Bruta'] = int(limpiar_valor_monetario(match_facturas.group(1)))
            datos['Total'] = int(limpiar_valor_monetario(match_facturas.group(2)))
        
        # Extraer Efectivo
        patron_efectivo = r'Medio\s*:\s*EFECTIVO[\s\S]*?Val\.\s*Ventas\s*:\s*\$?([\d,]+)'
        match_efectivo = re.search(patron_efectivo, contenido_texto)
        if match_efectivo:
            datos['Efectivo'] = int(limpiar_valor_monetario(match_efectivo.group(1)))
        
        # Extraer Datafono
        patron_datafono = r'Medio\s*:\s*DATAFONO[\s\S]*?Val\.\s*Ventas\s*:\s*\$?([\d,]+)'
        match_datafono = re.search(patron_datafono, contenido_texto)
        if match_datafono:
            datos['Datafono'] = int(limpiar_valor_monetario(match_datafono.group(1)))
        
        # Extraer Total de Egresos
        patron_egresos = r'DETALLE DE EGRESOS[\s\S]*?Total\s*:\s*\$?([\d,]+)'
        match_egresos = re.search(patron_egresos, contenido_texto)
        if match_egresos:
            datos['Total_Egresos'] = int(limpiar_valor_monetario(match_egresos.group(1)))
        
        # Extraer Diferencia
        patron_diferencia = r'Diferencia:\s*\$?([\d,]+)'
        match_diferencia = re.search(patron_diferencia, contenido_texto)
        if match_diferencia:
            datos['Diferencia'] = int(limpiar_valor_monetario(match_diferencia.group(1)))
            
    except Exception as e:
        st.error(f"Error al extraer datos: {e}")
    
    return datos

def procesar_pdf(archivo_pdf):
    """Procesa un archivo PDF y extrae los datos"""
    try:
        texto_completo = ""
        with pdfplumber.open(archivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto_completo += pagina.extract_text() + "\n"
        
        return extraer_datos_pdf(texto_completo)
    except Exception as e:
        st.error(f"Error al procesar PDF: {e}")
        return None

def get_download_link(df):
    """Genera un link de descarga para el DataFrame"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f'<a href="data:file/csv;base64,{b64}" download="datos_caja_{fecha_hora}.csv" class="download-button">📥 Descargar archivo CSV</a>'

# Interfaz principal
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📤 Sube tus archivos PDF")
    uploaded_files = st.file_uploader(
        "Arrastra o selecciona archivos PDF",
        type=['pdf'],
        accept_multiple_files=True,
        help="Puedes seleccionar múltiples archivos PDF a la vez"
    )

with col2:
    st.markdown("### 📊 Información")
    st.info("""
    **Datos que se extraen:**
    - Hora de Apertura
    - Hora de Cierre
    - Venta Bruta
    - Total
    - Efectivo
    - Datafono
    - Total Egresos
    - Diferencia
    """)

# Procesamiento de archivos
if uploaded_files:
    st.markdown("---")
    
    # Botón de procesar
    if st.button("🚀 Procesar PDFs", type="primary"):
        
        # Barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        resultados = []
        errores = []
        
        # Procesar cada archivo
        for idx, uploaded_file in enumerate(uploaded_files):
            # Actualizar progreso
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Procesando {idx + 1} de {len(uploaded_files)}: {uploaded_file.name}")
            
            # Extraer datos
            datos = procesar_pdf(uploaded_file)
            
            if datos:
                datos['Archivo'] = uploaded_file.name
                resultados.append(datos)
            else:
                errores.append(uploaded_file.name)
        
        # Limpiar barra de progreso
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if resultados:
            # Crear DataFrame
            df = pd.DataFrame(resultados)
            
            # Reordenar columnas
            columnas_orden = ['Archivo', 'Apertura', 'Cierre', 'V_Bruta', 'Total', 
                            'Efectivo', 'Datafono', 'Total_Egresos', 'Diferencia']
            df = df[columnas_orden]
            
            # Mensaje de éxito
            st.markdown(f"""
                <div class="success-message">
                    ✅ <strong>¡Proceso completado!</strong><br>
                    Se procesaron exitosamente {len(resultados)} de {len(uploaded_files)} archivos.
                </div>
            """, unsafe_allow_html=True)
            
            # Mostrar errores si los hay
            if errores:
                st.warning(f"⚠️ No se pudieron procesar los siguientes archivos: {', '.join(errores)}")
            
            # Mostrar preview de datos
            st.markdown("### 📋 Vista previa de los datos extraídos")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "V_Bruta": st.column_config.NumberColumn("V. Bruta", format="$%d"),
                    "Total": st.column_config.NumberColumn("Total", format="$%d"),
                    "Efectivo": st.column_config.NumberColumn("Efectivo", format="$%d"),
                    "Datafono": st.column_config.NumberColumn("Datafono", format="$%d"),
                    "Total_Egresos": st.column_config.NumberColumn("Total Egresos", format="$%d"),
                    "Diferencia": st.column_config.NumberColumn("Diferencia", format="$%d"),
                }
            )
            
            # Estadísticas rápidas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Ventas Brutas", f"${df['V_Bruta'].sum():,}")
            with col2:
                st.metric("Total Efectivo", f"${df['Efectivo'].sum():,}")
            with col3:
                st.metric("Total Datafono", f"${df['Datafono'].sum():,}")
            with col4:
                st.metric("Total Egresos", f"${df['Total_Egresos'].sum():,}")
            
            # Botón de descarga
            st.markdown("### 💾 Descargar resultados")
            st.markdown(get_download_link(df), unsafe_allow_html=True)
            
        else:
            st.markdown("""
                <div class="error-message">
                    ❌ <strong>Error:</strong> No se pudieron procesar los archivos.
                    Verifica que los PDFs tengan el formato correcto.
                </div>
            """, unsafe_allow_html=True)

else:
    # Instrucciones cuando no hay archivos
    st.markdown("""
        ### 👆 Para comenzar:
        1. Haz clic en el área de carga o arrastra tus archivos PDF
        2. Selecciona todos los PDFs que quieras procesar
        3. Haz clic en "Procesar PDFs"
        4. Descarga el archivo CSV con los resultados
        
        ---
        
        **Nota:** Esta aplicación procesa archivos de "COMPROBANTE INFORME DIARIO" 
        del sistema CONEXION POS.
    """)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666;">
        Extractor de Datos de Caja v1.0 | Desarrollado para MCAFE
    </div>
""", unsafe_allow_html=True)