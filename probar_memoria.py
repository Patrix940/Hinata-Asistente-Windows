
from memoria.memoria import obtener_recuerdos

recuerdos = obtener_recuerdos()

print("\n--- RECUERDOS GUARDADOS EN HINATA ---")

for recuerdo in recuerdos:
    print("\nID:", recuerdo[0])
    print("Categoría:", recuerdo[1])
    print("Contenido:", recuerdo[2])

print("\n--- FIN DE LA CONSULTA ---")
