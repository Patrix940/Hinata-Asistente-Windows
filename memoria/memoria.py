
from memoria.database import conectar_db


def guardar_recuerdo(categoria, contenido):
    """Guarda un recuerdo en la base de datos."""

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute(
        "INSERT INTO recuerdos (categoria, contenido) VALUES (?, ?)",
        (categoria, contenido)
    )

    conexion.commit()
    conexion.close()

    return True


def obtener_recuerdos(categoria=None):
    """Recupera los recuerdos guardados."""

    conexion = conectar_db()
    cursor = conexion.cursor()

    if categoria:
        cursor.execute(
            "SELECT id, categoria, contenido, fecha_creacion "
            "FROM recuerdos WHERE categoria = ? ORDER BY id DESC",
            (categoria,)
        )
    else:
        cursor.execute(
            "SELECT id, categoria, contenido, fecha_creacion "
            "FROM recuerdos ORDER BY id DESC"
        )

    recuerdos = cursor.fetchall()
    conexion.close()

    return recuerdos


def eliminar_recuerdo(id_recuerdo):
    """Elimina un recuerdo usando su identificador."""

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM recuerdos WHERE id = ?",
        (id_recuerdo,)
    )

    eliminado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return eliminado
