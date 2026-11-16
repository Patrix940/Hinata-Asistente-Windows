
from memoria.memoria import (
    guardar_recuerdo,
    obtener_recuerdos,
    actualizar_recuerdo,
    eliminar_recuerdo
)

# Crear un recuerdo temporal
guardar_recuerdo(
    "prueba_temporal",
    "Me gusta jugar Minecraft"
)

# Recuperar el recuerdo creado
recuerdos = obtener_recuerdos("prueba_temporal")

id_recuerdo = recuerdos[0][0]

# Actualizar su contenido
actualizar_recuerdo(
    id_recuerdo,
    "Ahora también me gusta jugar Valorant"
)

# Comprobar el resultado
resultado = obtener_recuerdos("prueba_temporal")

print("Recuerdo actualizado:")
print(resultado[0][2])

# Eliminar únicamente el recuerdo temporal
eliminar_recuerdo(id_recuerdo)

print("\nPrueba finalizada correctamente.")
