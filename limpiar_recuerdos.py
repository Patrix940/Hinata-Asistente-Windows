
import shutil
from memoria.database import conectar_db, RUTA_DB

# Crear una copia de seguridad antes de eliminar nada
ruta_respaldo = RUTA_DB.replace(
    "hinata.db",
    "hinata_respaldo.db"
)

shutil.copy2(RUTA_DB, ruta_respaldo)

print("Copia de seguridad creada correctamente.")

# Eliminar únicamente los cinco recuerdos de videojuegos
conexion = conectar_db()
cursor = conexion.cursor()

ids_eliminar = (5, 6, 10, 11, 12)

cursor.execute(
    """
    DELETE FROM recuerdos
    WHERE id IN (?, ?, ?, ?, ?)
    """,
    ids_eliminar
)

conexion.commit()

print("Recuerdos eliminados:", cursor.rowcount)

conexion.close()

print("Limpieza finalizada correctamente.")
