
import sqlite3
import os


# Obtener la ruta principal del proyecto
RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Crear la carpeta de datos si todavía no existe
RUTA_DATOS = os.path.join(RUTA_PROYECTO, "datos")
os.makedirs(RUTA_DATOS, exist_ok=True)

# Ruta donde se almacenará la base de datos
RUTA_DB = os.path.join(RUTA_DATOS, "hinata.db")


def conectar_db():
    """Conecta con la base de datos de Hinata."""
    conexion = sqlite3.connect(RUTA_DB)
    return conexion


def inicializar_db():
    """Crea la tabla de recuerdos si todavía no existe."""

    conexion = conectar_db()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recuerdos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            contenido TEXT NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conexion.commit()
    conexion.close()

