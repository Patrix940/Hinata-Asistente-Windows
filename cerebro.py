
import ollama

def preguntar_a_ia(mensaje):
    respuesta = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'system', 'content': 'Eres un asistente personal directo y eficiente.'},
            {'role': 'user', 'content': mensaje}
        ]
    )
    return respuesta['message']['content']

# Bucle básico de conversación
while True:
    orden = input("Tú: ")
    if orden.lower() in ['salir', 'exit']:
        break
    print("IA:", preguntar_a_ia(orden))
