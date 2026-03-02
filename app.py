import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CoffeeERP Intelligence Pro", layout="wide")

def conectar():
    conn = sqlite3.connect("finca_maestra.db", check_same_thread=False)
    cur = conn.cursor()
    
    # --- AUTO-REPARACIÓN DE TABLAS (Vital para la nube) ---
    # Tabla de Tareas
    cur.execute("""CREATE TABLE IF NOT EXISTS tareas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_programada TEXT, labor TEXT, lote TEXT, 
                    estado TEXT DEFAULT 'Pendiente')""")
    
    # Tabla de Inventario
    cur.execute("""CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT, cantidad REAL, unidad TEXT, costo_unit REAL)""")
    
    # Tabla de Diario Contable
    cur.execute("""CREATE TABLE IF NOT EXISTS diario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT, cuenta_id TEXT, detalle TEXT, 
                    debe REAL DEFAULT 0, haber REAL DEFAULT 0, lote TEXT)""")
    
    # Tabla de Cuentas (PUC)
    cur.execute("CREATE TABLE IF NOT EXISTS cuentas (codigo TEXT PRIMARY KEY, nombre TEXT)")
    
    # Insertar cuentas básicas si la tabla está vacía
    cur.execute("SELECT COUNT(*) FROM cuentas")
    if cur.fetchone()[0] == 0:
        cuentas = [('1105', 'Caja'), ('1430', 'Inventario'), ('4145', 'Ventas'), ('5105', 'Nómina')]
        cur.executemany("INSERT INTO cuentas VALUES (?,?)", cuentas)
        
    conn.commit()
    return conn

# --- FUNCIÓN PDF (RECIBOS) ---
def generar_recibo_pdf(nombre, labor, cantidad, total, fecha, lote):
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(5, 5, 200, 100)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="RECIBO DE PAGO - COFFEE-ERP", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, txt=f"Fecha: {fecha}", ln=True, align='R')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"TRABAJADOR: {nombre.upper()}", ln=True)
    pdf.cell(190, 10, txt=f"CONCEPTO: {labor} en {lote}", ln=True)
    pdf.cell(190, 10, txt=f"CANTIDAD: {cantidad} | VALOR: $ {total:,.0f}", ln=True)
    pdf.ln(10)
    pdf.cell(95, 10, txt="Firma Empleador: ________________", ln=False)
    pdf.cell(95, 10, txt="Firma Recibido: ________________", ln=True)
    
    pdf_output = pdf.output(dest="S").encode("latin-1")
    return base64.b64encode(pdf_output).decode("utf-8")

# --- SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso CoffeeERP")
        pwd = st.text_input("Clave Administrador", type="password")
        if st.button("Entrar"):
            if pwd == "cafe2024":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("Clave Incorrecta")
        return False
    return True

if check_password():
    st.sidebar.title("☕ Menú Pro")
    menu = ["📊 Dashboard Inteligente", "📅 Agenda de Labores", "📦 Inventario (Alertas)", "👨‍🌾 Nómina Pro", "💰 Ventas", "📄 Reportes"]
    opcion = st.sidebar.selectbox("Módulo", menu)

    # --- MÓDULO 1: DASHBOARD INTELIGENTE ---
    if opcion == "📊 Dashboard Inteligente":
        st.title("📊 Análisis de Rentabilidad y Alertas")
        conn = conectar()
        
        # Alerta de Tareas
        hoy = datetime.now().strftime("%Y-%m-%d")
        tareas_pend = pd.read_sql_query(f"SELECT * FROM tareas WHERE fecha_programada <= '{hoy}' AND estado='Pendiente'", conn)
        if not tareas_pend.empty:
            st.warning(f"🔔 Tienes {len(tareas_pend)} labores pendientes para hoy. Revisa la Agenda.")

        df = pd.read_sql_query("SELECT * FROM diario", conn)
        if not df.empty:
            ingresos = df[df['cuenta_id'] == '4145']['haber'].sum()
            gastos = df[df['cuenta_id'] == '5105']['debe'].sum()
            utilidad = ingresos - gastos
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Ingresos Totales", f"$ {ingresos:,.0f}")
            c2.metric("Inversión en Campo", f"$ {gastos:,.0f}", delta=f"-{gastos:,.0f}", delta_color="inverse")
            c3.metric("Utilidad Real", f"$ {utilidad:,.0f}")

            st.markdown("---")
            st.subheader("🧐 Análisis de Lotes")
            costos_por_lote = df[df['lote'].notnull()].groupby('lote')['debe'].sum()
            
            for lote, costo in costos_por_lote.items():
                if costo > (ingresos / 3 if ingresos > 0 else 1000000):
                    st.warning(f"⚠️ El **{lote}** tiene una inversión alta ($ {costo:,.0f}).")
                else:
                    st.success(f"✅ **{lote}** dentro de límites ($ {costo:,.0f}).")
            
            st.bar_chart(costos_por_lote)
        else:
            st.info("Sin datos financieros aún.")

    # --- MÓDULO 2: AGENDA DE LABORES ---
    elif opcion == "📅 Agenda de Labores":
        st.title("📅 Programación de Labores")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Agendar Tarea")
            with st.form("f_agenda"):
                f_tarea = st.date_input("Fecha")
                l_tarea = st.selectbox("Labor", ["Abon