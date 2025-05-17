# Crude Analyzer Pro – UTN-FRN INDUSTRIALIZACIÓN

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import os

# Configuración inicial
st.set_page_config(page_title="Crude Analyzer Pro - UTN-FRN", layout="wide")
LOGO_PATH = "logoutn.png"

# Estilo visual profesional
st.markdown("""
    <style>
        .stApp { background-color: #2d2d2d; color: #f0f0f0; }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        input, textarea, .stTextInput, .stNumberInput, .stSelectbox {
            background-color: #3c3c3c !important;
            color: white !important;
        }
        h1, h3 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=180)
    else:
        st.warning("⚠️ No se encontró el logo 'logoutn.png'")
    st.markdown("""
    ## 🛢️ Crude Analyzer Pro
    UTN-FRN · Ingeniería Química

    **Versión:** 2.1  
    **Desarrollado por:** Federico Catereniuc

    ---
    Esta herramienta permite:

    - 📊 Analizar curvas TBP
    - 🧪 Calcular Watson
    - 💰 Estimar ingresos por fracción
    - 🧠 Evaluar composición PONA
    """)

# Encabezado
st.markdown("""
    <h1 style='color:#4CAF50;'>🛢️ UTN-FRN INDUSTRIALIZACIÓN</h1>
    <h3>Sistema Profesional de Análisis de Crudos</h3>
""", unsafe_allow_html=True)

with st.expander("ℹ️ Introducción técnica al sistema"):
    st.markdown("""
    Esta aplicación fue desarrollada para profesionales e ingenieros que trabajan en la caracterización de crudos.

    ### Funcionalidades clave:
    - **Visualización de curvas TBP** (destilación a presión atmosférica).
    - **Cálculo del factor de Watson (Kw)** como indicador del tipo de crudo.
    - **Estimación de ingresos económicos por fracción** según rangos de temperatura.
    - **Análisis de composición PONA**, ideal para refinerías e I+D.

    > ⚙️ **Importancia**: estos análisis permiten evaluar la calidad del crudo, su valor de mercado, su comportamiento en procesos y su clasificación.
    """)

# Tabs
tabs = st.tabs(["📥 Datos del Crudo", "💰 Evaluación Económica", "🧪 Análisis PONA", "📄 Informe PDF"])

# Variables de estado
if "tbp_df" not in st.session_state:
    st.session_state.tbp_df = None
if "kw" not in st.session_state:
    st.session_state.kw = ""
if "api" not in st.session_state:
    st.session_state.api = ""
if "tipo_crudo" not in st.session_state:
    st.session_state.tipo_crudo = ""
if "ingresos" not in st.session_state:
    st.session_state.ingresos = ""
if "pona" not in st.session_state:
    st.session_state.pona = {}

# --- TAB 1: DATOS DEL CRUDOS ---
with tabs[0]:
    st.subheader("📥 Ingreso de datos del crudo")
    col1, col2 = st.columns(2)
    with col1:
        densidad = st.number_input("📦 Densidad a 15 °C [kg/m³]", value=850.0, min_value=600.0, max_value=1100.0)
    with col2:
        temp_k = st.number_input("🌡️ Temperatura media de ebullición TBP [K]", value=673.15, min_value=300.0, max_value=800.0)

    archivo = st.file_uploader("📂 Cargar curva TBP (.csv con columnas 'Temperatura' y 'Volumen')", type="csv")

    if archivo is not None:
        try:
            df = pd.read_csv(archivo)
        except Exception as e:
            st.error(f"❌ Error al leer el archivo TBP: {e}")
            df = pd.DataFrame()

        if "Temperatura" in df.columns and "Volumen" in df.columns:
            st.session_state.tbp_df = df
            st.success("✅ Curva TBP cargada correctamente.")

            fig, ax = plt.subplots(facecolor="#2d2d2d")
            ax.plot(df["Temperatura"], df["Volumen"], marker='o', linestyle='-', color='cyan')
            ax.set_facecolor("#2d2d2d")
            ax.set_xlabel("Temperatura [°C]", color="white")
            ax.set_ylabel("% Volumen Destilado", color="white")
            ax.set_title("Curva de Destilación TBP", color="white")
            ax.grid(True, color="gray")
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            st.pyplot(fig)

            dens_gcm3 = densidad / 1000
            kw = round((temp_k ** (1 / 3)) / dens_gcm3, 3)
            api = round((141.5 / (densidad / 1000)) - 131.5, 1)
            st.session_state.kw = kw
            st.session_state.api = api

            tipo = "🔵 Crudo Liviano" if api >= 40 else "🟡 Crudo Mediano" if api >= 25 else "🔴 Crudo Pesado"
            st.session_state.tipo_crudo = tipo

            st.metric("🧪 Factor de Watson", value=kw)
            st.metric("🧮 Grados API", value=api)
            st.success(f"🏷️ Clasificación: **{tipo}**")
        else:
            st.error("❌ El archivo debe tener exactamente las columnas: 'Temperatura' y 'Volumen'")
    else:
        st.info("📌 Cargá un archivo CSV con la curva TBP para continuar.")

# --- TAB 2: EVALUACIÓN ECONÓMICA ---
with tabs[1]:
    st.subheader("💰 Estimación de ingresos por fracción TBP")
    precios = {
        "<80°C (LPG-NL)": st.number_input("💸 Precio <80°C (LPG - Nafta Liviana)", value=25.0),
        "80–120°C (NL-NV)": st.number_input("💸 Precio 80–120°C", value=30.0),
        "120–180°C (NP)": st.number_input("💸 Precio 120–180°C", value=40.0),
        "180–360°C (GO+K)": st.number_input("💸 Precio 180–360°C", value=48.0),
        ">360°C (GOP+CR)": st.number_input("💸 Precio >360°C", value=28.0)
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

        tabla = []
        total = 0
        for fr, sub in fracciones.items():
            vol = sub["Volumen"].sum()
            ingreso = vol * precios[fr] / 100
            total += ingreso
            tabla.append({
                "Fracción": fr,
                "Volumen [%]": round(vol, 2),
                "Precio [USD/100 kg]": round(precios[fr], 2),
                "Ingreso Estimado [USD]": round(ingreso, 2)
            })

        df_ingresos = pd.DataFrame(tabla)
        st.dataframe(df_ingresos.style.format({
            "Volumen [%]": "{:.1f}",
            "Precio [USD/100 kg]": "${:.2f}",
            "Ingreso Estimado [USD]": "${:.2f}"
        }), use_container_width=True)
        st.metric("💰 Ingreso total estimado", f"${total:,.2f}")
        st.session_state.ingresos = df_ingresos
    else:
        st.warning("⚠️ Cargá la curva TBP primero.")

# --- TAB 3: PONA ---
with tabs[2]:
    st.subheader("🧪 Análisis PONA (Parafínicos, Olefínicos, Nafténicos, Aromáticos)")

    pona_csv = st.file_uploader("📁 Cargar CSV de composición PONA (opcional)", type="csv")
    fuente_csv = False

    if pona_csv:
        try:
            df_pona = pd.read_csv(pona_csv)
            paraf, olef, naft, arom = df_pona.iloc[0]
            fuente_csv = True
            st.success("✅ Composición cargada desde CSV.")
        except:
            paraf = olef = naft = arom = 0
            st.error("❌ Error en archivo CSV.")
    else:
        paraf = st.slider("🟦 % Parafínicos", 0, 100, 40)
        olef = st.slider("🟧 % Olefínicos", 0, 100, 5)
        naft = st.slider("🟨 % Nafténicos", 0, 100, 25)
        arom = st.slider("🟥 % Aromáticos", 0, 100, 30)

    total_pona = paraf + olef + naft + arom
    st.write(f"📊 Suma total: {total_pona}%")

    if total_pona != 100:
        st.error("⚠️ La suma debe ser 100%.")
        st.session_state.pona = {}
    else:
        fig, ax = plt.subplots()
        ax.pie([paraf, olef, naft, arom], labels=["Parafínicos", "Olefínicos", "Nafténicos", "Aromáticos"],
               autopct='%1.1f%%', startangle=90,
               colors=["#1f77b4", "#ff7f0e", "#ffdd57", "#d62728"])
        st.pyplot(fig)
        st.session_state.pona = {
            "Parafínicos": paraf,
            "Olefínicos": olef,
            "Nafténicos": naft,
            "Aromáticos": arom
        }

# --- TAB 4: PDF ---
with tabs[3]:
    st.subheader("📄 Generar Informe PDF Profesional")

    class PDF(FPDF):
        def header(self):
            if os.path.exists(LOGO_PATH):
                self.image(LOGO_PATH, 10, 8, 20)
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "UTN-FRN INDUSTRIALIZACIÓN - Crude Analyzer Pro", 0, 1, "C")
            self.set_font("Arial", "", 10)
            self.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "R")
            self.ln(4)

        def section(self, title, content):
            self.set_font("Arial", "B", 11)
            self.cell(0, 10, title, 0, 1)
            self.set_font("Arial", "", 10)
            if isinstance(content, str):
                self.multi_cell(0, 8, content.replace("–", "-"))
            elif isinstance(content, dict):
                for k, v in content.items():
                    self.multi_cell(0, 8, f"{k}: {v}%")
            elif isinstance(content, pd.DataFrame):
                for _, row in content.iterrows():
                    self.multi_cell(0, 8, f"{row['Fracción']}: {row['Volumen [%]']}% * ${row['Precio [USD/100 kg]']} = ${row['Ingreso Estimado [USD]']}")
            self.ln(2)

    if st.button("📥 Descargar Informe PDF"):
        try:
            pdf = PDF()
            pdf.add_page()
            pdf.section("🧪 Factor de Watson / API", f"{st.session_state.kw} Watson, {st.session_state.api}° API")
            pdf.section("🏷️ Clasificación del crudo", st.session_state.tipo_crudo)
            if isinstance(st.session_state.ingresos, pd.DataFrame):
                pdf.section("💰 Evaluación Económica", st.session_state.ingresos)
            if isinstance(st.session_state.pona, dict) and st.session_state.pona:
                pdf.section("🧪 Composición PONA", st.session_state.pona)

            buffer = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            buffer.write(pdf_bytes)
            buffer.seek(0)
            st.download_button("📄 Descargar Informe PDF", data=buffer, file_name="informe_crudo.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"❌ Error al generar el PDF: {e}")
