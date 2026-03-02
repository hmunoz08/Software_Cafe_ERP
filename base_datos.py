import sqlite3

def crear_sistema_contable():
    conn = sqlite3.connect("finca_maestra.db")
    cur = conn.cursor()
    
    # 1. TABLA DE CUENTAS (PUC)
    cur.execute("CREATE TABLE IF NOT EXISTS cuentas (codigo TEXT PRIMARY KEY, nombre TEXT)")
    
    # 2. LIBRO DIARIO (El corazón contable)
    cur.execute("""CREATE TABLE IF NOT EXISTS diario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT, cuenta_id TEXT, detalle TEXT, 
                    debe REAL DEFAULT 0, haber REAL DEFAULT 0, lote TEXT)""")

    # 3. KARDEX (Inventario de abonos y café)
    cur.execute("""CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT, cantidad REAL, unidad TEXT, costo_unit REAL)""")
    
    # Insertamos las cuentas contables estándar
    cuentas = [('1105', 'Caja'), ('1430', 'Inventario'), ('4145', 'Ventas'), ('5105', 'Nómina')]
    cur.executemany("INSERT OR IGNORE INTO cuentas VALUES (?,?)", cuentas)
    
    conn.commit()
    conn.close()
    print("Cerebro (Base de datos) listo.")

if __name__ == "__main__":
    crear_sistema_contable()
import sqlite3
conn = sqlite3.connect("finca_maestra.db")
cur = conn.cursor()
# Creamos la tabla de tareas/agenda
cur.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_programada TEXT,
        labor TEXT,
        lote TEXT,
        estado TEXT DEFAULT 'Pendiente'
    )
""")
conn.commit()
conn.close()
print("Tabla de tareas lista.")