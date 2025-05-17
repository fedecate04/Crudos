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

# Mostrar encabezado
col1, col2 = st.columns([1, 9])
with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
with col2:
    st.markdown("""
    <h1 style='margin-bottom:0;'>UTN-FRN INDUSTRIALIZACIÓN</h1>
    <h3 style='margin-top:0;'>Crude Analyzer Pro</h3>
    """, unsafe_allow_html=True)

# Introducción
st.markdown("""
    <hr>
    <p>Esta herramienta profesional permite caracterizar crudos utilizando su curva TBP (destilación), calcular el factor de Watson, estimar ingresos económicos por fracción y analizar la composición PONA (Parafínicos, Olefínicos, Nafténicos y Aromáticos).</p>
    <ul>
        <li><strong>Densidad</strong>: Usada para calcular el factor de Watson.</li>
        <li><strong>Curva TBP</strong>: Representa el porcentaje de volumen destilado a distintas temperaturas.</li>
        <li><strong>Watson (Kw)</strong>: Indica el tipo de crudo. Kw &gt; 12: parafínico, Kw &lt; 10: aromático.</li>
        <li><strong>Ingreso estimado</strong>: Calculado en base a precios por fracción.</li>
        <li><strong>PONA</strong>: Analiza el perfil químico del crudo.</li>
    </ul>
    <p>🌡️ <strong>Dew Point</strong>: Punto de rocío, donde comienzan a condensarse hidrocarburos.</p>
    <p>❄️ <strong>Sad Point</strong>: Punto donde las ceras comienzan a cristalizar, importante para transporte.</p>
    <hr>
""", unsafe_allow_html=True)

# Tabs principales
tabs = st.tabs(["📥 Datos del Crudo", "💰 Evaluación Económica", "🧪 Análisis PONA", "📄 Informe PDF"])

if "tbp_df" not in st.session_state:
    st.session_state.tbp_df = None
if "kw" not in st.session_state:
    st.session_state.kw = ""
if "ingresos" not in st.session_state:
    st.session_state.ingresos = ""
if "pona" not in st.session_state:
    st.session_state.pona = {}

# --- TAB 1: Datos del Crudo --- #
with tabs[0]:
    st.subheader("📥 Ingreso de datos técnicos")

    densidad = st.number_input("Densidad a 15 °C [kg/m³]", value=850.0, help="Usada para calcular el factor de Watson")
    temp_k = st.number_input("Temperatura promedio de ebullición TBP [K]", value=673.15, help="Promedio ponderado de la curva TBP")

    archivo = st.file_uploader("📂 Cargar curva TBP (.csv con columnas 'Temperatura' y 'Volumen')", type=["csv"])

    if archivo is not None:
        df = pd.read_csv(archivo)
        if "Temperatura" in df.columns and "Volumen" in df.columns:
            st.session_state.tbp_df = df
            st.success("Curva TBP cargada correctamente.")

            fig, ax = plt.subplots()
            ax.plot(df["Temperatura"], df["Volumen"], marker="o")
            ax.set_xlabel("Temperatura [°C]")
            ax.set_ylabel("% Volumen Destilado")
            ax.set_title("Curva TBP")
            ax.grid(True)
            st.pyplot(fig)

            dens_gcm3 = densidad / 1000
            kw = round((temp_k ** (1/3)) / dens_gcm3, 3)
            st.session_state.kw = kw
            st.markdown(f"<h2 style='color:#4CAF50;'>🧪 Factor de Watson: {kw}</h2>", unsafe_allow_html=True)
        else:
            st.error("El archivo debe tener columnas 'Temperatura' y 'Volumen'")

# --- TAB 2: Evaluación Económica --- #
with tabs[1]:
    st.subheader("💰 Estimación de ingresos por fracción")

    precios = {
        "<80°C (LPG-NL)": st.number_input("<80°C (LPG-NL) [USD/bbl]", value=0.0),
        "80–120°C (NL-NV)": st.number_input("80–120°C (NL-NV) [USD/bbl]", value=30.0),
        "120–180°C (NP)": st.number_input("120–180°C (NP) [USD/bbl]", value=40.0),
        "180–360°C (GO+K)": st.number_input("180–360°C (GO+K) [USD/bbl]", value=48.0),
        ">360°C (GOP+CR)": st.number_input(">360°C (GOP+CR) [USD/bbl]", value=28.0)
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
        for fraccion, subset in fracciones.items():
            vol = subset["Volumen"].sum()
            ingreso = vol * precios[fraccion] / 100
            total += ingreso
            texto += f"{fraccion}: {vol:.1f}% * ${precios[fraccion]:.2f} = ${ingreso:.2f}\n"
        texto += f"\nTotal estimado: ${total:.2f}"
        st.session_state.ingresos = texto
        st.text_area("🧾 Detalle del cálculo económico", texto, height=180)
    else:
        st.warning("Primero debés cargar una curva TBP válida en la pestaña anterior.")

# --- TAB 3: Análisis PONA --- #
with tabs[2]:
    st.subheader("🧪 Composición PONA (%)")

    parafinicos = st.slider("% Parafínicos", 0, 100, 40)
    olefinicos = st.slider("% Olefínicos", 0, 100, 5)
    naftenicos = st.slider("% Nafténicos", 0, 100, 25)
    aromaticos = st.slider("% Aromáticos", 0, 100, 30)
    total_pona = parafinicos + olefinicos + naftenicos + aromaticos

    if total_pona != 100:
        st.warning(f"⚠️ La suma total es {total_pona}%. Debe ser exactamente 100%.")
    else:
        st.success("✅ Composición válida.")
        fig, ax = plt.subplots()
        labels = ["Parafínicos", "Olefínicos", "Nafténicos", "Aromáticos"]
        values = [parafinicos, olefinicos, naftenicos, aromaticos]
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.set_title("Distribución PONA")
        st.pyplot(fig)

    st.session_state.pona = {
        "Parafínicos": parafinicos,
        "Olefínicos": olefinicos,
        "Nafténicos": naftenicos,
        "Aromáticos": aromaticos
    }

# --- TAB 4: PDF --- #
with tabs[3]:
    st.subheader("📄 Exportar informe profesional")

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

    if st.button("📥 Descargar informe en PDF"):
        pdf = PDF()
        pdf.add_page()
        pdf.section("Factor de Watson", str(st.session_state.kw))
        pdf.section("Evaluación Económica", st.session_state.ingresos)
        pdf.section("Análisis PONA", st.session_state.pona)

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)

        st.download_button(
            label="📄 Descargar Informe PDF",
            data=buffer,
            file_name="informe_crudo.pdf",
            mime="application/pdf"
        )

