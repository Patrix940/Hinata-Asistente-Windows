
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
    """Recupera recuerdos por categoría.
    Si no encuentra coincidencias, devuelve todos los recuerdos.
    """

    conexion = conectar_db()
    cursor = conexion.cursor()

    if categoria:
        cursor.execute(
            """
            SELECT id, categoria, contenido, fecha_creacion
            FROM recuerdos
            WHERE LOWER(categoria) = LOWER(?)
            ORDER BY id DESC
            """,
            (categoria,)
        )

        recuerdos = cursor.fetchall()

        # Si no encuentra la categoría, consulta todos los recuerdos.
        if not recuerdos:
            cursor.execute(
                """
                SELECT id, categoria, contenido, fecha_creacion
                FROM recuerdos
                ORDER BY id DESC
                """
            )
            recuerdos = cursor.fetchall()

    else:
        cursor.execute(
            """
            SELECT id, categoria, contenido, fecha_creacion
            FROM recuerdos
            ORDER BY id DESC
            """
        )
        recuerdos = cursor.fetchall()

    conexion.close()

    return recuerdos


def actualizar_recuerdo(id_recuerdo: int, nuevo_contenido: str):
    """Actualiza un recuerdo usando su ID numérico y el contenido nuevo."""

    conexion = conectar_db()
    cursor = conexion.cursor()

    # Buscar el recuerdo existente
    cursor.execute(
        "SELECT contenido FROM recuerdos WHERE id = ?",
        (id_recuerdo,)
    )

    resultado = cursor.fetchone()

    if resultado is None:
        conexion.close()
        return False

    contenido_anterior = resultado[0]

    # Evitar guardar información repetida
    if nuevo_contenido.lower() in contenido_anterior.lower():
        conexion.close()
        return True

    # Agregar la información nueva
    contenido_actualizado = (
        contenido_anterior + ". También le gusta " + nuevo_contenido
    )

    # Guardar el recuerdo actualizado
    cursor.execute(
        "UPDATE recuerdos SET contenido = ? WHERE id = ?",
        (contenido_actualizado, id_recuerdo)
    )

    conexion.commit()
    conexion.close()

    return True

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
