# app_streamlit_crudos.py

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from scipy.interpolate import interp1d
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile

# Propiedades base
PRECIOS = {"<80°C": 10, "80–120°C": 30, "120–180°C": 40, "180–360°C": 48, ">360°C": 28}
CORTES = list(PRECIOS.keys())

# Funciones principales
def celsius_to_rankine(temp_c):
    return (temp_c + 273.15) * 9 / 5

def calcular_kw(tb_c, densidad_rel):
    tb_r = celsius_to_rankine(tb_c)
    return round((tb_r ** (1/3)) / densidad_rel, 3)

def clasificar_kw(kw):
    if kw > 12.5:
        return 'Parafínico'
    elif kw < 10.5:
        return 'Nafténico'
    else:
        return 'Intermedio'

def clasificar_flashpoint(fp):
    if fp < 23:
        return "🔥 Clase I (muy inflamable)"
    elif fp < 60:
        return "⚠️ Clase II (riesgo moderado)"
    else:
        return "✅ Clase III (poco inflamable)"

def estimar_flash(fracs):
    livianos = fracs["<80°C"] + fracs["80–120°C"]
    if livianos > 40:
        return 20
    elif livianos > 20:
        return 40
    else:
        return 70

def calcular_ingreso(fracs):
    return sum((fracs[k] * PRECIOS[k]) / 100 for k in CORTES)

def analizar_crudo(nombre, dens, tb, temp, evap):
    f = interp1d(temp, evap, kind='linear', fill_value='extrapolate')
    fracs = {
        "<80°C": float(f(80)),
        "80–120°C": float(f(120)) - float(f(80)),
        "120–180°C": float(f(180)) - float(f(120)),
        "180–360°C": float(f(360)) - float(f(180)),
        ">360°C": 100 - float(f(360))
    }
    api = round((141.5 / dens) - 131.5, 2)
    kw = calcular_kw(tb, dens)
    tipo = clasificar_kw(kw)
    fp = estimar_flash(fracs)
    clase_fp = clasificar_flashpoint(fp)
    ingreso = calcular_ingreso(fracs)
    return {
        "Nombre": nombre,
        "Densidad": dens,
        "API": api,
        "Tb": tb,
        "Kw": kw,
        "Tipo": tipo,
        "Flash Point": fp,
        "Clase": clase_fp,
        "Ingreso": ingreso,
        "Fracciones": fracs,
        "Temp": temp,
        "Evap": evap
    }

# PDF
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Informe Comparativo de Crudos", 0, 1, 'C')

    def add_crudo(self, data):
        self.set_font("Arial", 'B', 11)
        self.cell(0, 8, data["Nombre"], 0, 1)
        self.set_font("Arial", '', 10)
        for k in ["Densidad", "API", "Tb", "Kw", "Tipo", "Flash Point", "Clase", "Ingreso"]:
            self.cell(0, 8, f"{k}: {data[k]}", 0, 1)
        self.set_font("Arial", 'I', 9)
        self.cell(0, 6, "Distribución estimada por cortes TBP:", 0, 1)
        for corte, val in data['Fracciones'].items():
            self.cell(0, 6, f"{corte}: {val:.2f}%", 0, 1)
        self.ln(3)

    def add_tbp_chart(self, filepath):
        self.image(filepath, w=180)
        self.ln(5)

# Streamlit app
st.set_page_config("Comparador de Crudos", layout="wide")
st.title("🛢️ Comparador Profesional de Crudos")

with st.expander("ℹ️ ¿Qué cálculos realiza esta aplicación?"):
    st.markdown("""
    Esta herramienta analiza y compara diferentes crudos con base en los siguientes parámetros:

    - **Densidad**: Se utiliza para calcular los grados API.
    - **API**: Calculado como \
