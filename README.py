# BLABO BALANCE PRO - APP EN STREAMLIT PARA TESIS FINALBLABO BALANCE PRO - APP EN STREAMLIT PARA TESIS FINAL

import streamlit
as st import pandas 
as pd import numpy 
as np from io 
import BytesIO

#CONFIGURACION GENERAL

st.set_page_config(page_title="BLABO Balance Pro", layout="wide") st.title("🛢️ BLABO Balance Pro - Simulador Técnico de Limpieza de Tanques")

#INTRODUCCION

with st.expander("📘 Introducción al Sistema BLABO", expanded=True): st.markdown(""" El sistema BLABO® permite la limpieza automatizada de tanques de almacenamiento de crudo sin ingreso de personal, recuperando hidrocarburos, removiendo lodo parafínico y separando agua y sólidos.

Esta aplicación simula el balance de masa y energía de cada módulo del sistema, con visualización de fórmulas
y generación automática de un informe PDF al finalizar.
""")

#ENTRADA DE DATOS

st.sidebar.header("🔧 Parámetros de Entrada") with st.sidebar.form("input_form"): V_tanque = st.number_input("Capacidad del tanque (m³)", value=10000) H_lodo = st.number_input("Altura del lodo (m)", value=4.0) densidad_lodo = st.number_input("Densidad del lodo (kg/m³)", value=950) HC_pct = st.slider("% Hidrocarburos", 0, 100, 70) agua_pct = st.slider("% Agua", 0, 100, 15) sol_inorg_pct = st.slider("% Sólidos inorgánicos", 0, 100, 10) sol_org_pct = st.slider("% Sólidos orgánicos", 0, 100, 5) temp_ini = st.number_input("Temperatura inicial (°C)", value=20) temp_fin = st.number_input("Temperatura objetivo (°C)", value=80) caudal_recirc = st.number_input("Caudal de recirculación (m³/h)", value=100) submit = st.form_submit_button("Calcular")

if submit: # CALCULOS BASE volumen_lodo = V_tanque * H_lodo / H_lodo  # simplificado masa_total = volumen_lodo * densidad_lodo

masas = {
    "Hidrocarburos": masa_total * HC_pct / 100,
    "Agua": masa_total * agua_pct / 100,
    "Sólidos inorgánicos": masa_total * sol_inorg_pct / 100,
    "Sólidos orgánicos": masa_total * sol_org_pct / 100
}

st.success("Datos cargados y cálculos iniciales realizados")
st.write(f"**Masa total del lodo:** {masa_total:,.0f} kg")
st.write("**Composición del lodo:**")
st.dataframe(pd.DataFrame(masas, index=["kg"]).T)

st.markdown("---")
st.header("⚙️ Cálculos por Módulo")

# Ejemplo: MODULO 2 - RECIRCULACION
st.subheader("Módulo 2 - Recirculación + Hidrociclones")
st.markdown("""
Este módulo recircula aceite/lodo calentado para disolver el fondo del tanque. Parte del fluido va a boquillas,
y parte al sistema de separación. Se calienta mediante vapor indirecto.
""")

m_recirc = caudal_recirc * 900  # flujo másico aproximado
Cp_aceite = 2.1
Q = m_recirc * Cp_aceite * (temp_fin - temp_ini)

st.latex(r"Q = \dot{m} \cdot C_p \cdot \Delta T")
st.markdown(f"Donde: \n- \dot{{m}} = {m_recirc:,.0f} kg/h \n- C_p = {Cp_aceite} kJ/kg·K \n- \Delta T = {temp_fin - temp_ini} °C")

st.success(f"Energía térmica requerida: {Q/1000:,.2f} MW")

st.markdown("---")
st.header("📄 Resultado Final y Exportación")
resumen = f"""

Masa total del lodo: {masa_total:,.0f} kg\n Composición:\n- Hidrocarburos: {masas['Hidrocarburos']:,.0f} kg\n- Agua: {masas['Agua']:,.0f} kg\n- Sólidos inorgánicos: {masas['Sólidos inorgánicos']:,.0f} kg\n- Sólidos orgánicos: {masas['Sólidos orgánicos']:,.0f} kg\n\nMódulo 2 - Recirculación:\n- Caudal másico: {m_recirc:,.0f} kg/h\n- Energía térmica estimada: {Q/1000:,.2f} MW"""

buffer = BytesIO()
buffer.write(resumen.encode())
buffer.seek(0)

st.download_button(
    label="📥 Descargar resumen en TXT",
    data=buffer,
    file_name="Resumen_Balance_BLABO.txt",
    mime="text/plain"
)

