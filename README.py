# Crudos
app_streamlit_crudos.py

import streamlit as st import pandas as pd import numpy as np from io import BytesIO from scipy.interpolate import interp1d from fpdf import FPDF import matplotlib.pyplot as plt import tempfile

Propiedades base

PRECIOS = {"<80°C": 10, "80–120°C": 30, "120–180°C": 40, "180–360°C": 48, ">360°C": 28} CORTES = list(PRECIOS.keys())

Funciones principales

def celsius_to_rankine(temp_c): return (temp_c + 273.15) * 9/5

def calcular_kw(tb_c, densidad_rel): tb_r = celsius_to_rankine(tb_c) return round((tb_r ** (1/3)) / densidad_rel, 3)

def clasificar_kw(kw): if kw > 12.5: return 'Parafínico' elif kw < 10.5: return 'Nafténico' else: return 'Intermedio'

def clasificar_flashpoint(fp): if fp < 23: return "🔥 Clase I (muy inflamable)" elif fp < 60: return "⚠️ Clase II (riesgo moderado)" else: return "✅ Clase III (poco inflamable)"

def estimar_flash(fracs): livianos = fracs["<80°C"] + fracs["80–120°C"] if livianos > 40: return 20 elif livianos > 20: return 40 else: return 70

def calcular_ingreso(fracs): return sum((fracs[k] * PRECIOS[k]) / 100 for k in CORTES)

def analizar_crudo(nombre, dens, tb, temp, evap): f = interp1d(temp, evap, kind='linear', fill_value='extrapolate') fracs = { "<80°C": float(f(80)), "80–120°C": float(f(120)) - float(f(80)), "120–180°C": float(f(180)) - float(f(120)), "180–360°C": float(f(360)) - float(f(180)), ">360°C": 100 - float(f(360)) } api = round((141.5 / dens) - 131.5, 2) kw = calcular_kw(tb, dens) tipo = clasificar_kw(kw) fp = estimar_flash(fracs) clase_fp = clasificar_flashpoint(fp) ingreso = calcular_ingreso(fracs) return { "Nombre": nombre, "Densidad": dens, "API": api, "Tb": tb, "Kw": kw, "Tipo": tipo, "Flash Point": fp, "Clase": clase_fp, "Ingreso": ingreso, "Fracciones": fracs, "Temp": temp, "Evap": evap }

PDF

class PDF(FPDF): def header(self): self.set_font("Arial", 'B', 12) self.cell(0, 10, "Informe Comparativo de Crudos", 0, 1, 'C')

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

App Streamlit

st.set_page_config("Comparador de Crudos", layout="wide") st.title("🛢️ Comparador Profesional de Crudos")

with st.expander("ℹ️ ¿Qué cálculos realiza esta aplicación?"): st.markdown(""" Esta herramienta analiza y compara diferentes crudos con base en los siguientes parámetros:

- **Densidad**: Se utiliza para calcular los grados API.
- **API**: Calculado como \text{API} = \frac{141.5}{\text{densidad}} - 131.5.
- **Kw (Factor de Watson)**: Calculado como Kw = \frac{Tb^{1/3}}{\text{densidad}}, clasifica el tipo de crudo.
- **Fracciones TBP**: Se interpolan los % evaporados a 80, 120, 180 y 360 °C para estimar los cortes por rango de ebullición.
- **Ingreso estimado**: Se calcula ponderando las fracciones por un valor económico por corte.
- **Flash Point**: Estimado en base a la fracción liviana del crudo.
- **Clase de inflamabilidad**: Basado en el flash point.

Todos los resultados se pueden visualizar en tabla y se exportan en un informe PDF con una gráfica comparativa de las curvas TBP.
""")

n = st.number_input("Cantidad de crudos a comparar:", 2, 6, 2) crudos = []

for i in range(n): st.markdown(f"### Crudo #{i+1}") nombre = st.text_input(f"Nombre crudo #{i+1}", f"Crudo_{i+1}") dens = st.number_input(f"Densidad relativa #{i+1}", 0.75, 0.95, 0.85, step=0.0001) tb = st.number_input(f"Temperatura ebullición media #{i+1} (°C)", 100.0, 600.0, 300.0) csv = st.file_uploader(f"Cargar curva TBP #{i+1} (.csv con Temp, %Evap)", type="csv", key=f"csv{i}") if csv: df = pd.read_csv(csv) temp = df.iloc[:,0].dropna().values evap = df.iloc[:,1].dropna().values try: datos = analizar_crudo(nombre, dens, tb, temp, evap) crudos.append(datos) st.success(f"Crudo {nombre} cargado correctamente") except Exception as e: st.error(f"Error procesando curva: {e}")

if len(crudos) == n: st.markdown("---") st.header("📊 Resultados Comparativos") df_comp = pd.DataFrame([{k: v[k] for k in v if k not in ['Fracciones', 'Temp', 'Evap']} for v in crudos]) st.dataframe(df_comp, use_container_width=True)

st.subheader("📉 Comparación de Curvas TBP")
fig, ax = plt.subplots(figsize=(8, 4))
for cr in crudos:
    ax.plot(cr['Temp'], cr['Evap'], label=cr['Nombre'])
ax.set_xlabel('Temperatura (°C)')
ax.set_ylabel('% Evaporado')
ax.set_title('Curvas TBP comparativas')
ax.grid(True)
ax.legend()
st.pyplot(fig)

st.header("📥 Informe PDF")
if st.button("Generar informe PDF"):
    pdf = PDF()
    pdf.add_page()
    for cr in crudos:
        pdf.add_crudo(cr)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    fig.savefig(tmpfile.name, bbox_inches='tight')
    pdf.add_tbp_chart(tmpfile.name)

    buffer = BytesIO()
    pdf.output(buffer)
    st.download_button("📄 Descargar PDF", buffer.getvalue(), file_name="informe_crudos.pdf", mime="application/pdf")

