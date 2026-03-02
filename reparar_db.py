import sqlite3

def reparar():
    conn = sqlite3.connect("finca_maestra.db")
    cur = conn.cursor()
    
    print("Iniciando reparación de base de datos...")
    
    # 1. Creamos la tabla de tareas (la que te está dando el error)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_programada TEXT,
            labor TEXT,
            lote TEXT,
            estado TEXT DEFAULT 'Pendiente'
        )
    """)
    
    # 2. Verificamos que las otras tablas existan (por seguridad)
    cur.execute("CREATE TABLE IF NOT EXISTS cuentas (codigo TEXT PRIMARY KEY, nombre TEXT)")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS diario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT, cuenta_id TEXT, detalle TEXT, 
                    debe REAL DEFAULT 0, haber REAL DEFAULT 0, lote TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT, cantidad REAL, unidad TEXT, costo_unit REAL)""")
    
    conn.commit()
    conn.close()
    print("✅ ¡Reparación exitosa! La tabla 'tareas' ya existe.")

if __name__ == "__main__":
    reparar()