import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CoffeeERP Intelligence Pro", layout="wide")

def conectar():
    return sqlite3.connect("finca_maestra.db", check_same_thread=False)

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
    # Añadimos "📅 Agenda de Labores" al menú
    menu = ["📊 Dashboard Inteligente", "📅 Agenda de Labores", "📦 Inventario (Alertas)", "👨‍🌾 Nómina Pro", "💰 Ventas", "📄 Reportes"]
    opcion = st.sidebar.selectbox("Módulo", menu)

    # --- MÓDULO 1: DASHBOARD INTELIGENTE ---
    if opcion == "📊 Dashboard Inteligente":
        st.title("📊 Análisis de Rentabilidad y Alertas")
        conn = conectar()
        
        # --- NUEVA SECCIÓN: ALERTA DE TAREAS ---
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

    # --- MÓDULO 2: AGENDA DE LABORES (NUEVO) ---
    elif opcion == "📅 Agenda de Labores":
        st.title("📅 Programación de Labores")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Agendar Tarea")
            with st.form("f_agenda"):
                f_tarea = st.date_input("Fecha")
                l_tarea = st.selectbox("Labor", ["Abonada", "Fumigación", "Deshierbe", "Poda", "Mantenimiento"])
                lt_tarea = st.selectbox("Lote", ["Lote 1", "Lote 2", "Lote 3"])
                if st.form_submit_button("Guardar en Agenda"):
                    conn = conectar(); cur = conn.cursor()
                    cur.execute("INSERT INTO tareas (fecha_programada, labor, lote) VALUES (?,?,?)", 
                                (f_tarea.strftime("%Y-%m-%d"), l_tarea, lt_tarea))
                    conn.commit(); st.success("Tarea agendada"); st.rerun()

        with col2:
            st.subheader("Pendientes")
            conn = conectar()
            df_t = pd.read_sql_query("SELECT * FROM tareas WHERE estado='Pendiente' ORDER BY fecha_programada ASC", conn)
            for i, r in df_t.iterrows():
                with st.expander(f"📌 {r['labor']} - {r['fecha_programada']}"):
                    st.write(f"Lote: {r['lote']}")
                    if st.button("Marcar como Hecho", key=f"btn_{r['id']}"):
                        cur = conn.cursor()
                        cur.execute("UPDATE tareas SET estado='Completada' WHERE id=?", (r['id'],))
                        conn.commit(); st.rerun()

    # --- MÓDULO 3: INVENTARIO ---
    elif opcion == "📦 Inventario (Alertas)":
        st.title("📦 Gestión de Almacén")
        conn = conectar()
        df_stock = pd.read_sql_query("SELECT item, SUM(cantidad) as stock FROM inventario GROUP BY item", conn)
        
        if not df_stock.empty:
            cols = st.columns(3)
            for i, row in df_stock.iterrows():
                with cols[i % 3]:
                    if row['stock'] <= 2: st.error(f"🔴 {row['item']}: {row['stock']} unid.")
                    elif row['stock'] <= 5: st.warning(f"🟡 {row['item']}: {row['stock']} unid.")
                    else: st.success(f"🟢 {row['item']}: {row['stock']} unid.")

        with st.form("compra_insumo"):
            st.subheader("Registrar Entrada")
            item = st.text_input("Producto")
            cant = st.number_input("Cantidad", min_value=1.0)
            valor = st.number_input("Costo Total", min_value=0.0)
            if st.form_submit_button("Cargar Stock"):
                cur = conn.cursor(); f = datetime.now().strftime("%Y-%m-%d")
                cur.execute("INSERT INTO inventario (item, cantidad, unidad, costo_unit) VALUES (?,?,'UN',?)", (item, cant, valor/cant))
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, debe) VALUES (?,?,'Compra Insumo',?)", (f, '1430', valor))
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, haber) VALUES (?,?,'Salida Caja',?)", (f, '1105', valor))
                conn.commit(); st.success("Inventario actualizado"); st.rerun()

    # --- MÓDULO 4: NÓMINA ---
    elif opcion == "👨‍🌾 Nómina Pro":
        st.title("👨‍🌾 Registro de Pagos")
        with st.form("f_nomina"):
            n = st.text_input("Trabajador")
            lab = st.selectbox("Labor", ["Recolección", "Abonada", "Limpia"])
            lot = st.selectbox("Lote", ["Lote 1", "Lote 2", "Lote 3"])
            can = st.number_input("Cantidad", min_value=0.0)
            pre = st.number_input("Precio", value=800)
            if st.form_submit_button("Liquidar"):
                total = can * pre; f = datetime.now().strftime("%Y-%m-%d")
                conn = conectar(); cur = conn.cursor()
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, debe, lote) VALUES (?,?,?,?,?)", (f, '5105', f"Pago {n}", total, lot))
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, haber) VALUES (?,?,'Salida Nómina',?)", (f, '1105', total))
                conn.commit()
                
                pdf_b64 = generar_recibo_pdf(n, lab, can, total, f, lot)
                st.success(f"✅ Pagado: ${total:,.0f}")
                st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="Recibo_{n}.pdf" style="padding:10px; background:green; color:white; border-radius:5px; text-decoration:none;">📥 Descargar Recibo</a>', unsafe_allow_html=True)

    # --- MÓDULO 5: VENTAS ---
    elif opcion == "☕ Ventas":
        st.title("💰 Ingresos")
        with st.form("f_ventas"):
            cli = st.text_input("Cliente")
            mon = st.number_input("Monto", min_value=0.0)
            if st.form_submit_button("Registrar Venta"):
                conn = conectar(); cur = conn.cursor(); f = datetime.now().strftime("%Y-%m-%d")
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, debe) VALUES (?,?,'Venta Café',?)", (f, '1105', mon))
                cur.execute("INSERT INTO diario (fecha, cuenta_id, detalle, haber) VALUES (?,?,'Ingreso Venta',?)", (f, '4145', mon))
                conn.commit(); st.balloons(); st.success("Venta guardada")

    # --- MÓDULO 6: REPORTES ---
    elif opcion == "📄 Reportes":
        st.title("📄 Libros Contables")
        conn = conectar()
        df = pd.read_sql_query("SELECT * FROM diario ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "contabilidad.csv", "text/csv")