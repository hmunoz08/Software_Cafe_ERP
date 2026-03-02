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
    
    # --- AUTO-CREACIÓN DE TABLAS (Evita errores en la nube) ---
    cur.execute("""CREATE TABLE IF NOT EXISTS tareas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_programada TEXT, labor TEXT, lote TEXT, 
                    estado TEXT DEFAULT 'Pendiente')""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT, cantidad REAL, unidad TEXT, costo_unit REAL)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS diario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT, cuenta_id TEXT, detalle TEXT, 
                    debe REAL DEFAULT 0, haber REAL DEFAULT 0, lote TEXT)""")
    
    cur.execute("CREATE TABLE IF NOT EXISTS cuentas (codigo TEXT PRIMARY KEY, nombre TEXT)")
    
    # Insertar cuentas si la tabla está vacía
    cur.execute("SELECT COUNT(*) FROM cuentas")
    if cur.fetchone()[0] == 0:
        cuentas = [('1105', 'Caja'), ('1430', 'Inventario'), ('4145', 'Ventas'), ('5105', 'Nómina')]
        cur.executemany("INSERT INTO cuentas VALUES (?,?)", cuentas)
        
    conn.commit()
    return conn

# --- FUNCIÓN PDF ---
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
    menu = ["📊 Dashboard", "📅 Agenda", "📦 Inventario", "👨‍🌾 Nómina", "💰 Ventas", "📄 Reportes"]
    opcion = st.sidebar.selectbox("Módulo", menu)

    conn = conectar()

    # --- MÓDULO 1: DASHBOARD ---
    if opcion == "📊 Dashboard":
        st.title("📊 Resumen de la Finca")
        
        # Alerta de Tareas
        hoy = datetime.now().strftime("%Y-%m-%d")
        try:
            tareas_pend = pd.read_sql_query(f"SELECT * FROM tareas WHERE fecha_programada <= '{hoy}' AND estado='Pendiente'", conn)
            if not tareas_pend.empty:
                st.warning(f"🔔 Tienes {len(tareas_pend)} labores pendientes.")
        except:
            st.info("Configurando agenda por primera vez...")

        df = pd.read_sql_query("SELECT * FROM diario", conn)
        if not df.empty:
            ing = df[df['cuenta_id'] == '4145']['haber'].sum()
            gas = df[df['cuenta_id'] == '5105']['debe'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Ingresos Totales", f"$ {ing:,.0f}")
            c2.metric("Gastos Nómina", f"$ {gas:,.0f}", delta=f"-{gas:,.0f}", delta_color="inverse")
            st.bar_chart(df[df['lote'].notnull()].groupby('lote')['debe'].sum())

    # --- MÓDULO 2: AGENDA ---
    elif opcion == "📅 Agenda":
        st.title("📅 Programación de Labores")
        with st.form("f_agenda"):
            f_tarea = st.date_input("Fecha")
            l_tarea = st.selectbox("Labor", ["Abonada", "Fumigación", "Deshierbe", "Poda"])
            lt_tarea = st.selectbox("Lote", ["Lote 1", "Lote 2", "Lote 3"])
            if st.form_submit_button("Agendar"):
                cur = conn.cursor()
                cur.execute("INSERT INTO tareas (fecha_programada, labor, lote) VALUES (?,?,?)", 
                            (f_tarea.strftime("%Y-%m-%d"), l_tarea, lt_tarea))
                conn.commit()
                st.success("Tarea guardada")
                st.rerun()

    # --- MÓDULO 3: INVENTARIO ---
    elif opcion == "📦 Inventario":
        st.title("📦 Inventario")
        df_i = pd.read_sql_query("SELECT item, SUM(cantidad) as stock FROM inventario GROUP BY item", conn)
        st.dataframe(df_i)
        with st.form("f_inv"):
            it = st.text_input("Producto")
            can = st.number_input("Cantidad", min_value=1.0)
            val = st.number_input("Costo Total", min_value=0.0)
            if st.form_submit_button("Registrar"):
                cur = conn.cursor()
                cur.execute("INSERT INTO inventario (item, cantidad, unidad, costo_unit) VALUES (?,?,'UN',?)", (it, can, val/can if can>0 else 0))
                conn.commit()
                st.rerun()

    # --- MÓDULO 4: NÓMINA ---
    elif opcion == "👨‍🌾 Nómina":
        st.title("👨‍🌾 Pagos")
        with st.form("f_nom"):
            n = st.text_input("Trabajador")
            lab = st.selectbox("Trabajo", ["Recolección", "Limpia"])
            lot = st.selectbox("Lote", ["Lote 1", "Lote 2", "Lote 3"])
            can = st.number_input("Cantidad", min_value=0.0)
            pre = st.number_input("Precio", value=800)
            if st.form_submit_button("Pagar y Generar PDF"):
                tot = can * pre
                f = datetime.now().strftime("%Y-%m-%d")
                cur = conn.cursor()
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, debe, lote) VALUES (?,?,?,?,?)", (f, '5105', f"Pago {n}", tot, lot))
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, haber) VALUES (?,?,'Salida Caja',?)", (f, '1105', tot))
                conn.commit()
                pdf_b64 = generar_recibo_pdf(n, lab, can, tot, f, lot)
                st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="Recibo_{n}.pdf" style="padding:10px; background:green; color:white; border-radius:5px; text-decoration:none;">📥 Descargar Recibo</a>', unsafe_allow_html=True)

    # --- MÓDULO 5: VENTAS ---
    elif opcion == "💰 Ventas":
        st.title("💰 Registrar Venta de Café")
        with st.form("f_v"):
            val_v = st.number_input("Monto Venta", min_value=0.0)
            if st.form_submit_button("Vender"):
                f = datetime.now().strftime("%Y-%m-%d")
                cur = conn.cursor()
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, debe) VALUES (?,?,'Venta Café',?)", (f, '1105', val_v))
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, haber) VALUES (?,?,'Ingreso Venta',?)", (f, '4145', val_v))
                conn.commit()
                st.success("Venta registrada")

    # --- MÓDULO 6: REPORTES ---
    elif opcion == "📄 Reportes":
        st.title("📄 Historial Contable")
        df_r = pd.read_sql_query("SELECT * FROM diario ORDER BY id DESC", conn)
        st.dataframe(df_r)