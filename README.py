# UTN-FRN INDUSTRIALIZACIÓN - Crude Analyzer Pro (Streamlit)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import os

# Configuración inicial
st.set_page_config(page_title="Crude Analyzer Pro - UTN-FRN", layout="wide")
LOGO_PATH = "utnlogo.png"

# Sidebar profesional
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.warning("⚠️ No se encontró el logo 'utnlogo.png'")
    st.markdown("""
    ## 🛢️ Crude Analyzer Pro
    UTN-FRN · Ingeniería Química

    **Versión:** 2.0
    **Autor:** Federico Catereniuc

    Esta app permite:
    - 📊 Analizar curvas TBP
    - 🧪 Calcular Watson
    - 💰 Estimar ingresos
    - 🧠 Evaluar composición PONA

    📩 Contacto: federico@example.com
    """)

# Encabezado
st.markdown("""
    <h1 style='text-align:center; color:#4CAF50;'>🛢️ UTN-FRN INDUSTRIALIZACIÓN</h1>
    <h3 style='text-align:center;'>Sistema de Análisis Profesional de Crudos</h3>
""", unsafe_allow_html=True)

# Introducción técnica
with st.expander("ℹ️ Ver introducción al sistema"):
    st.markdown("""
    Esta herramienta profesional permite:
    - Cargar y visualizar curvas TBP.
    - Calcular el factor de Watson.
    - Estimar ingresos por fracción.
    - Analizar composiciones químicas PONA (Parafínicos, Olefínicos, Nafténicos, Aromáticos).

    ### 🧪 Parámetros Clave
    - **Densidad [kg/m³]**: usada para clasificar el crudo.
    - **TBP**: curva de % de destilado vs temperatura.
    - **Watson (Kw)**: relaciona densidad y punto medio de ebullición.
    - **Dew Point / Sad Point**: indicadores de condensación y cristalización (visual).
    - **Ingreso económico**: estimación por fracción.
    - **PONA**: perfil químico para clasificación de hidrocarburos.
    """)

# Tabs
tabs = st.tabs(["📥 Datos del Crudo", "💰 Evaluación Económica", "🧪 Análisis PONA", "📄 Informe PDF"])

# Variables de estado
if "tbp_df" not in st.session_state:
    st.session_state.tbp_df = None
if "kw" not in st.session_state:
    st.session_state.kw = ""
if "ingresos" not in st.session_state:
    st.session_state.ingresos = ""
if "pona" not in st.session_state:
    st.session_state.pona = {}

# TAB 1 - CARGA DE DATOS
with tabs[0]:
    st.subheader("📥 Ingreso de datos del crudo")

    col1, col2 = st.columns(2)
    with col1:
        densidad = st.number_input("Densidad a 15 °C [kg/m³]", value=850.0, help="Usada para calcular el factor de Watson")
    with col2:
        temp_k = st.number_input("Temperatura media de ebullición TBP [K]", value=673.15, help="Promedio ponderado de TBP")

    archivo = st.file_uploader("📂 Cargar curva TBP (.csv con columnas 'Temperatura' y 'Volumen')", type="csv")

    if archivo is not None:
        try:
            df = pd.read_csv(archivo)
        except Exception as e:
            st.error(f"❌ Error al leer el archivo TBP: {e}")
            df = pd.DataFrame()
        if "Temperatura" in df.columns and "Volumen" in df.columns:
            st.session_state.tbp_df = df
            st.success("Curva TBP cargada correctamente.")

            fig, ax = plt.subplots()
            ax.plot(df["Temperatura"], df["Volumen"], marker='o')
            ax.set_xlabel("Temperatura [°C]")
            ax.set_ylabel("% Volumen Destilado")
            ax.set_title("Curva TBP")
            ax.grid(True)
            st.pyplot(fig)

            dens_gcm3 = densidad / 1000
            kw = round((temp_k ** (1/3)) / dens_gcm3, 3)
            st.session_state.kw = kw
            st.metric("🧪 Factor de Watson", value=kw)
        else:
            st.error("El archivo debe tener columnas 'Temperatura' y 'Volumen'")

# TAB 2 - INGRESOS ECONÓMICOS
with tabs[1]:
    st.subheader("💰 Estimación de ingresos por fracción TBP")

    precios = {
        "<80°C (LPG-NL)": st.number_input("Precio <80°C (LPG-NL)", value=0.0),
        "80–120°C (NL-NV)": st.number_input("Precio 80–120°C", value=30.0),
        "120–180°C (NP)": st.number_input("Precio 120–180°C", value=40.0),
        "180–360°C (GO+K)": st.number_input("Precio 180–360°C", value=48.0),
        ">360°C (GOP+CR)": st.number_input("Precio >360°C", value=28.0)
    }

    if st.session_state.tbp_df is not None:
        df = st.session_state.tbp_df
        fracciones = {
            "<80°C (LPG-NL)": df[df["Temperatura"] < 80],
            "80–120°C (NL-NV)": df[(df["Temperatura"] >= 80) & (df["Temperatura"] < 120)],
            "120–180°C (NP)": df[(df["Temperatura"] >= 120) & (df["Temperatura"] < 180)],
            "180–360°C (GO+K)": df[(df["Temperatura"] >= 180) & (df["Temperatura"] < 360)],
            ">360°C (GOP+CR)": df[df["Temperatura"] >= 360]
        }
        texto = ""
        total = 0
        for fr, sub in fracciones.items():
            vol = sub["Volumen"].sum()
            ingreso = vol * precios[fr] / 100
            total += ingreso
            texto += f"{fr}: {vol:.1f}% * ${precios[fr]:.2f} = ${ingreso:.2f}\n"
        texto += f"\nTotal estimado: ${total:.2f}"
        st.session_state.ingresos = texto
        st.code(texto)
        st.metric("Total estimado", f"${total:.2f}")
    else:
        st.warning("Primero cargá una curva TBP válida.")

# TAB 3 - ANÁLISIS PONA
with tabs[2]:
    st.subheader("🧪 Análisis PONA (Parafínicos - Olefínicos - Nafténicos - Aromáticos)")

    pona_csv = st.file_uploader("📁 Cargar CSV de composición PONA (opcional)", type="csv")

    if pona_csv:
        try:
            df_pona = pd.read_csv(pona_csv)
            if not all(col in df_pona.columns for col in ['Parafínicos', 'Olefínicos', 'Nafténicos', 'Aromáticos']):
                raise ValueError("Faltan columnas necesarias en el archivo CSV")
            paraf, olef, naft, arom = df_pona.iloc[0]
        except Exception as e:
            st.error(f"❌ Error al leer el archivo PONA: {e}")
            paraf = olef = naft = arom = 0
    else:
        paraf = st.slider("% Parafínicos", 0, 100, 40)
        olef = st.slider("% Olefínicos", 0, 100, 5)
        naft = st.slider("% Nafténicos", 0, 100, 25)
        arom = st.slider("% Aromáticos", 0, 100, 30)

    total_pona = paraf + olef + naft + arom
    if total_pona != 100:
        st.warning(f"⚠️ Suma total = {total_pona}%. Ajustá para llegar a 100%.")
    else:
        fig, ax = plt.subplots()
        ax.pie([paraf, olef, naft, arom], labels=["Parafínicos", "Olefínicos", "Nafténicos", "Aromáticos"], autopct='%1.1f%%')
        ax.set_title("Distribución PONA")
        st.pyplot(fig)
        st.session_state.pona = {"Parafínicos": paraf, "Olefínicos": olef, "Nafténicos": naft, "Aromáticos": arom}

# TAB 4 - EXPORTAR PDF
with tabs[3]:
    st.subheader("📄 Generar Informe Profesional en PDF")

    class PDF(FPDF):
        def header(self):
            if os.path.exists(LOGO_PATH):
                self.image(LOGO_PATH, 10, 8, 20)
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "UTN-FRN INDUSTRIALIZACIÓN - Crude Analyzer Pro", 0, 1, "C")
            self.set_font("Arial", "", 10)
            self.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "R")
            self.ln(5)
        def section(self, title, content):
            self.set_font("Arial", "B", 11)
            self.cell(0, 10, title, 0, 1)
            self.set_font("Arial", "", 10)
            if isinstance(content, str):
                self.multi_cell(0, 8, content)
            elif isinstance(content, dict):
                for k, v in content.items():
                    self.multi_cell(0, 8, f"{k}: {v}%")
            self.ln(2)

    if st.button("📥 Descargar Informe PDF"):
        try:
            pdf = PDF()
            pdf.add_page()
            pdf.section("Factor de Watson", str(st.session_state.kw))
            pdf.section("Evaluación Económica", st.session_state.ingresos)
            pdf.section("Análisis PONA", st.session_state.pona)

            buffer = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            buffer.write(pdf_bytes)
            buffer.seek(0)

            st.download_button(
                label="📄 Descargar PDF",
                data=buffer,
                file_name="informe_crudo.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"❌ Error al generar el PDF: {e}")



