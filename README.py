# Crude Analyzer Pro - Tkinter App

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF
import os
from datetime import datetime

# Crear carpeta para informes
os.makedirs("informes", exist_ok=True)

# Clase PDF profesional
class PDFInforme(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "INFORME DE CARACTERIZACIÓN DE CRUDOS", 0, 1, "C")
        self.set_font("Arial", "", 10)
        self.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "R")
        self.ln(5)

    def section(self, title, content):
        self.set_font("Arial", "B", 11)
        self.cell(0, 10, title, 0, 1)
        self.set_font("Arial", "", 10)
        if isinstance(content, str):
            self.multi_cell(0, 8, content)
        elif isinstance(content, list):
            for item in content:
                self.multi_cell(0, 8, f"- {item}")
        self.ln(2)

# Clase principal de la aplicación
class CrudeAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crude Analyzer Pro - Caracterización de Crudos")
        self.root.geometry("1100x750")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.data = {}
        self.kw_resultado = ""
        self.resultado_ingresos = ""

        self._crear_tab_datos()
        self._crear_tab_resultados()
        self._crear_tab_economico()
        self._crear_tab_foda()
        self._crear_tab_exportar()

    def _crear_tab_datos(self):
        self.tab_datos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_datos, text="Ingreso de Datos")

        ttk.Label(self.tab_datos, text="Densidad a 15°C (kg/m³):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.densidad_entry = ttk.Entry(self.tab_datos)
        self.densidad_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.tab_datos, text="Temperatura promedio de ebullición TBP (K):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.temp_tb_entry = ttk.Entry(self.tab_datos)
        self.temp_tb_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.tab_datos, text="Cargar curva TBP (CSV)").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Button(self.tab_datos, text="📂 Cargar TBP", command=self.cargar_tbp).grid(row=2, column=1, padx=5, pady=5)

    def _crear_tab_resultados(self):
        self.tab_resultados = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_resultados, text="Resultados Técnicos")

        self.resultados_text = tk.Text(self.tab_resultados, height=15)
        self.resultados_text.pack(fill="x", padx=10, pady=10)

        self.canvas_frame = ttk.Frame(self.tab_resultados)
        self.canvas_frame.pack(fill="both", expand=True)

        ttk.Button(self.tab_resultados, text="Calcular", command=self.calcular).pack(pady=10)

    def _crear_tab_economico(self):
        self.tab_economico = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_economico, text="Evaluación Económica")

        ttk.Label(self.tab_economico, text="Precio por fracción (USD/bbl)").grid(row=0, column=0, columnspan=2, pady=5)
        self.precios = {
            "<80°C (LPG-NL)": tk.DoubleVar(value=0.0),
            "80–120°C (NL-NV)": tk.DoubleVar(value=30.0),
            "120–180°C (NP)": tk.DoubleVar(value=40.0),
            "180–360°C (GO+K)": tk.DoubleVar(value=48.0),
            ">360°C (GOP+CR)": tk.DoubleVar(value=28.0)
        }
        for i, (k, var) in enumerate(self.precios.items()):
            ttk.Label(self.tab_economico, text=k).grid(row=i+1, column=0, sticky="e", padx=5, pady=2)
            ttk.Entry(self.tab_economico, textvariable=var).grid(row=i+1, column=1, padx=5, pady=2)

        ttk.Button(self.tab_economico, text="Calcular Ingreso Estimado", command=self.calcular_ingreso).grid(row=7, column=0, columnspan=2, pady=10)
        self.resultado_economico = tk.Text(self.tab_economico, height=10)
        self.resultado_economico.grid(row=8, column=0, columnspan=2, padx=10, pady=5)

    def _crear_tab_foda(self):
        self.tab_foda = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_foda, text="Análisis FODA")

        self.foda_entries = {}
        for i, label in enumerate(["Fortalezas", "Oportunidades", "Debilidades", "Amenazas"]):
            ttk.Label(self.tab_foda, text=label).grid(row=i*2, column=0, sticky="w", padx=10)
            text = tk.Text(self.tab_foda, height=4, width=80)
            text.grid(row=i*2+1, column=0, padx=10, pady=5)
            self.foda_entries[label] = text

    def _crear_tab_exportar(self):
        self.tab_exportar = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_exportar, text="Informe PDF")
        ttk.Button(self.tab_exportar, text="📄 Exportar Informe PDF", command=self.exportar_pdf).pack(pady=20)

    def cargar_tbp(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                self.data['tbp'] = pd.read_csv(file_path)
                messagebox.showinfo("Carga exitosa", "Curva TBP cargada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")

    def calcular(self):
        try:
            densidad = float(self.densidad_entry.get()) / 1000  # kg/m³ a g/cm³
            temp_ebullicion = float(self.temp_tb_entry.get())  # Kelvin
            kw = round((temp_ebullicion ** (1 / 3)) / densidad, 3)
            self.kw_resultado = f"Factor de Watson: {kw}"

            self.resultados_text.delete("1.0", tk.END)
            self.resultados_text.insert(tk.END, self.kw_resultado + "\n")

            if 'tbp' in self.data:
                self.graficar_tbp()
        except Exception as e:
            messagebox.showerror("Error de cálculo", str(e))

    def graficar_tbp(self):
        df = self.data['tbp']
        if 'Temperatura' in df.columns and 'Volumen' in df.columns:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.plot(df['Temperatura'], df['Volumen'], marker='o')
            ax.set_title("Curva TBP")
            ax.set_xlabel("Temperatura [°C]")
            ax.set_ylabel("% Volumen Destilado")
            ax.grid(True)

            for widget in self.canvas_frame.winfo_children():
                widget.destroy()

            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            messagebox.showwarning("Columnas faltantes", "El archivo debe tener columnas 'Temperatura' y 'Volumen'.")

    def calcular_ingreso(self):
        if 'tbp' not in self.data:
            messagebox.showwarning("Datos faltantes", "Primero cargá la curva TBP.")
            return
        df = self.data['tbp']
        fracciones = {
            "<80°C (LPG-NL)": df[df['Temperatura'] < 80],
            "80–120°C (NL-NV)": df[(df['Temperatura'] >= 80) & (df['Temperatura'] < 120)],
            "120–180°C (NP)": df[(df['Temperatura'] >= 120) & (df['Temperatura'] < 180)],
            "180–360°C (GO+K)": df[(df['Temperatura'] >= 180) & (df['Temperatura'] < 360)],
            ">360°C (GOP+CR)": df[df['Temperatura'] >= 360]
        }
        resultados = ""
        total_ingreso = 0
        for fraccion, subset in fracciones.items():
            volumen_total = subset['Volumen'].sum()
            precio = self.precios[fraccion].get()
            ingreso = volumen_total * precio / 100  # % volumen a fracción
            total_ingreso += ingreso
            resultados += f"{fraccion}: {volumen_total:.1f}% -> ${ingreso:.2f}\n"

        resultados += f"\nIngreso total estimado: ${total_ingreso:.2f}"
        self.resultado_ingresos = resultados
        self.resultado_economico.delete("1.0", tk.END)
        self.resultado_economico.insert(tk.END, resultados)

    def exportar_pdf(self):
        pdf = PDFInforme()
        pdf.add_page()
        pdf.section("Resultados Técnicos", self.kw_resultado)
        pdf.section("Evaluación Económica", self.resultado_ingresos)
        foda = {}
        for k, v in self.foda_entries.items():
            foda[k] = v.get("1.0", tk.END).strip()
        for k in ["Fortalezas", "Oportunidades", "Debilidades", "Amenazas"]:
            pdf.section(k, foda[k].splitlines())
        output_path = os.path.join("informes", "informe_crudo.pdf")
        pdf.output(output_path)
        messagebox.showinfo("PDF Exportado", f"Informe guardado en {output_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CrudeAnalyzerApp(root)
    root.mainloop()
