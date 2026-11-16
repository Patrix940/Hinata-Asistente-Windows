import io
import json
import queue
import wave
import webrtcvad
import unicodedata
import time
import numpy as np
import collections
import ollama
import pyttsx3
import sounddevice as sd
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
from herramientas import abrir_programa, crear_nota, ver_hora_actual
# Sistema de memoria de hinata
from memoria.database import inicializar_db
from memoria.memoria import (
    guardar_recuerdo,
    obtener_recuerdos,
    actualizar_recuerdo,
    eliminar_recuerdo
)

# Inicializar la base de datos de Hinata
inicializar_db()

print("[Memoria de Hinata inicializada correctamente]")

# Función de voz robusta y limpia para evitar bloqueos
def hablar(texto):
    print(f"Hinata: {texto}")
    try:
        motor = pyttsx3.init()
        motor.setProperty('rate', 175)
        motor.say(texto)
        motor.runAndWait()
        motor.stop()
    except Exception as e:
        print(f"Error en voz (TTS): {e}")

# 2. Cargar el modelo offline de Vosk para escuchar la palabra clave
print("Cargando modelo de escucha en segundo plano...")
modelo_vosk = Model("modelo_voz")
cola_audio = queue.Queue()

def callback_audio(indata, frames, time, status):
    """Recibe bloques de audio del micrófono en tiempo real."""
    cola_audio.put(bytes(indata))

def esperar_palabra_clave():
    """Escucha en tiempo real y muestra lo que interpreta para detectar la palabra clave al instante."""
    reconocedor = KaldiRecognizer(modelo_vosk, 16000)
    # Agregamos más aproximaciones fonéticas en español por si dice "Hinata"
    variaciones_clave = ["hinata", "inata", "jinata", "renata", "ginata", "nata", "sinata", "y nata", "asistente"]
    
    print("\n[Modo reposo: Di 'Hinata' para activar...]")
    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16', channels=1, callback=callback_audio):
        while True:
            datos = cola_audio.get()
            if reconocedor.AcceptWaveform(datos):
                resultado = json.loads(reconocedor.Result())
                texto = resultado.get("text", "").lower()
            else:
                parcial = json.loads(reconocedor.PartialResult())
                texto = parcial.get("partial", "").lower()
            
            if texto:
                print(f"Escuchando: {texto}", end="\r")
                if any(palabra in texto for palabra in variaciones_clave):
                    print() # Salto de línea limpio
                    return True

def escuchar_orden():
    """Graba la orden completa durante 5 segundos tras despertar."""
    print("[¡Te escucho! Di tu orden ahora...]")
    fs = 16000
    duracion = 5
    
    try:
        audio_data = sd.rec(int(duracion * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(audio_data.tobytes())
        
        wav_io.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)
            texto = recognizer.recognize_google(audio, language="es-ES")
            print(f"Tú: {texto}")
            return texto
            
    except sr.UnknownValueError:
        hablar("No alcancé a entenderte.")
        return ""
    except Exception as e:
        print(f"Error de audio: {e}")
        return ""

# 3. Configuración de herramientas y Ollama

mis_herramientas = [
    abrir_programa,
    crear_nota,
    ver_hora_actual,
    guardar_recuerdo,
    obtener_recuerdos,
    actualizar_recuerdo,
    eliminar_recuerdo
]

mapa_funciones = {
    "abrir_programa": abrir_programa,
    "crear_nota": crear_nota,
    "ver_hora_actual": ver_hora_actual,
    "guardar_recuerdo": guardar_recuerdo,
    "obtener_recuerdos": obtener_recuerdos,
    "actualizar_recuerdo": actualizar_recuerdo,
    "eliminar_recuerdo": eliminar_recuerdo
}


def procesar_orden(mensaje):
    # Detectar preguntas relacionadas con la hora
    mensaje_normalizado = unicodedata.normalize(
        "NFD", mensaje.lower()
    )

    mensaje_normalizado = "".join(
        c for c in mensaje_normalizado
        if unicodedata.category(c) != "Mn"
    )

    # Detectar solicitudes de actualización de recuerdos
    solicitud_actualizacion = any(
        frase in mensaje_normalizado
        for frase in [
            "actualiza",
            "actualizar",
            "actualiza mis recuerdos",
            "modifica mi recuerdo",
            "modificar mi recuerdo",
            "corrige mi recuerdo",
            "corrige mis recuerdos"
        ]
    )

    frases_hora = [
        "que hora es",
        "dime la hora",
        "dime que hora",
        "me dices la hora",
        "ver hora actual",
        "hora actual",
        "que hora tienes",
        "sabes que hora es"
    ]

    if any(frase in mensaje_normalizado for frase in frases_hora):
        print("[Ejecutando: ver_hora_actual]")
        return ver_hora_actual()

    
    # Actualizar directamente los gustos de videojuegos
    # cuando el usuario indica que también le gusta otro juego.
    if (
        solicitud_actualizacion
        and "tambien me gusta jugar" in mensaje_normalizado
    ):
        nuevo_contenido = mensaje_normalizado.split(
            "tambien me gusta jugar", 1
        )[1]

        for terminador in [
            " actualiza",
            " actualizar",
            " modifica",
            " modificar",
            " corrige",
            " corregir"
        ]:
            nuevo_contenido = nuevo_contenido.split(
                terminador, 1
            )[0]

        nuevo_contenido = nuevo_contenido.strip(" .,!?¿¡")

        if not nuevo_contenido:
            return "No pude identificar el videojuego que quieres agregar."

        recuerdos = obtener_recuerdos()

        recuerdos_juegos = [
            recuerdo for recuerdo in recuerdos
            if recuerdo[1].strip().lower() == "juegos favoritos"
        ]

        if len(recuerdos_juegos) != 1:
            return (
                "No pude identificar un único recuerdo de juegos favoritos. "
                "No modifiqué ningún recuerdo."
            )

        id_correcto = recuerdos_juegos[0][0]

        print(
            f"[Actualizando recuerdo de videojuegos: "
            f"ID {id_correcto} -> {nuevo_contenido}]"
        )

        resultado = actualizar_recuerdo(
            id_correcto,
            nuevo_contenido
        )

        if resultado:
            return (
                f"Listo. Agregué {nuevo_contenido} "
                "a tus juegos favoritos sin borrar los anteriores."
            )

        return "No pude actualizar el recuerdo."


    mensajes = [
        {
            'role': 'system',
            'content': """
Eres Hinata, un asistente personal de Windows.
Responde de forma breve, amable y natural para ser leída en voz alta.

Tu objetivo es ayudar al usuario, comprender sus necesidades y recordar información importante para futuras conversaciones.


SISTEMA DE MEMORIA:

Tienes acceso a cuatro herramientas de memoria:

- guardar_recuerdo(categoria, contenido)
- obtener_recuerdos(categoria)
- actualizar_recuerdo(id_recuerdo, nuevo_contenido)
- eliminar_recuerdo(id_recuerdo)

Debes gestionar tu memoria de forma inteligente siguiendo estas reglas:

1. Cuando el usuario comparta información personal estable, preferencias, gustos, objetivos o información importante sobre sus proyectos, evalúa si merece ser recordada.

2. Si la información es útil para futuras conversaciones y no está almacenada, guárdala utilizando guardar_recuerdo.

3. No guardes saludos, preguntas comunes, comentarios triviales, información temporal ni datos que ya estén almacenados.

4. Nunca guardes contraseñas, credenciales ni información personal sensible.

5. Antes de responder preguntas sobre información personal, proyectos, preferencias o recuerdos anteriores, consulta obtener_recuerdos cuando sea pertinente.

6. Si no conoces la categoría exacta de un recuerdo, utiliza obtener_recuerdos() sin argumentos para consultar todos los recuerdos almacenados.

7. Nunca inventes recuerdos ni afirmes recordar información que no hayas encontrado.

8. Cuando el usuario solicite modificar o actualizar un recuerdo, primero ejecuta obtener_recuerdos() sin argumentos para consultar todos los recuerdos.

9. Los recuerdos devueltos contienen cuatro datos: ID, categoría, contenido y fecha. El ID siempre es el primer dato y es un número entero.

10. Para utilizar actualizar_recuerdo, debes copiar exactamente el ID numérico del recuerdo encontrado. Nunca utilices el nombre de la categoría, el contenido del recuerdo ni texto inventado como identificador.

11. El parámetro id_recuerdo debe contener exclusivamente el número del ID. El parámetro nuevo_contenido debe contener únicamente la información nueva que se desea agregar o actualizar, no toda la frase que dijo el usuario.

12. Si el usuario dice "también", conserva la información anterior y agrega la nueva. Si solicita reemplazar o corregir un dato, modifica únicamente la información correspondiente.

13. Si existen varios recuerdos relacionados y no puedes identificar con seguridad cuál modificar, pregunta al usuario antes de actualizar.

14. Nunca afirmes que actualizaste un recuerdo si la herramienta devuelve False.


HERRAMIENTAS:

Puedes utilizar las herramientas disponibles para abrir programas, crear notas y consultar la hora.

Antes de ejecutar una herramienta, verifica que la acción corresponda a lo que solicita el usuario.

Responde siempre de manera natural y breve.
"""
        },
        {'role': 'user', 'content': mensaje}
    ]

    # Permitir varias rondas de herramientas
    for intento in range(5):

        respuesta = ollama.chat(
            model='llama3.1',
            messages=mensajes,
            tools=mis_herramientas
        )

        llamadas = respuesta['message'].get('tool_calls')

        # Si no necesita más herramientas, devuelve la respuesta
        if not llamadas:
            return respuesta['message']['content']

        mensajes.append(respuesta['message'])

        # Ejecutar las herramientas solicitadas
        for llamada in llamadas:

            nombre_funcion = llamada['function']['name']
            argumentos = llamada['function']['arguments']

            print(f"[Ejecutando: {nombre_funcion} -> {argumentos}]")

            # Bloquear guardados cuando se solicita actualizar
            if solicitud_actualizacion and nombre_funcion == "guardar_recuerdo":

                print("[Protección: guardado bloqueado porque solicitaste actualizar]")

                recuerdos = obtener_recuerdos()

                resultado = (
                    "El guardado fue bloqueado porque el usuario solicitó actualizar "
                    "un recuerdo existente.\n"
                    "Estos son los recuerdos disponibles con sus ID reales:\n"
                    + str(recuerdos)
                    + "\nDebes identificar el recuerdo relacionado con la solicitud "
                    "y utilizar actualizar_recuerdo con su ID numérico. "
                    "No inventes IDs ni guardes un recuerdo nuevo."
                )

                mensajes.append({
                    'role': 'tool',
                    'content': str(resultado)
                })

                continue

            funcion_real = mapa_funciones[nombre_funcion]

            # Validar el ID antes de actualizar un recuerdo
            if nombre_funcion == "actualizar_recuerdo":

                id_recuerdo = argumentos.get("id_recuerdo")

                if not str(id_recuerdo).isdigit():
                    resultado = (
                        "Error: el ID del recuerdo no es válido. "
                        "Debes consultar los recuerdos y obtener su ID numérico."
                    )

                else:
                    argumentos["id_recuerdo"] = int(id_recuerdo)

                    recuerdos = obtener_recuerdos()

                    ids_validos = [
                        recuerdo[0] for recuerdo in recuerdos
                    ]

                    if argumentos["id_recuerdo"] not in ids_validos:
                        resultado = (
                            "Error: el ID del recuerdo no existe. "
                            "Debes consultar los recuerdos y obtener su ID numérico."
                        )
                    else:
                        resultado = funcion_real(**argumentos)

            else:
                resultado = funcion_real(**argumentos)

            mensajes.append({
                'role': 'tool',
                'content': str(resultado)
            })

    return "No pude completar la operación. Inténtalo nuevamente."




def grabar_orden_segura(duracion=20):
    """
    Graba una orden detectando automáticamente la voz
    y finaliza cuando detecta suficiente silencio.
    """

    fs = 16000
    frame_ms = 30
    frame_size = int(fs * frame_ms / 1000)

    silencio_final = 1200
    voz_minima = 300

    frames_silencio = int(silencio_final / frame_ms)
    frames_voz = int(voz_minima / frame_ms)
    max_frames = int(duracion * 1000 / frame_ms)

    vad = webrtcvad.Vad(2)

    audio_frames = []
    hablando = False
    contador_voz = 0
    contador_silencio = 0

    print("[Hinata está escuchando... Habla ahora]")

    try:
        with sd.InputStream(
            samplerate=fs,
            channels=1,
            dtype="int16",
            blocksize=frame_size
        ) as stream:

            for _ in range(max_frames):

                audio_data, overflowed = stream.read(frame_size)

                if overflowed:
                    print("[Aviso: se perdió un fragmento de audio]")

                frame = audio_data.tobytes()

                tiene_voz = vad.is_speech(frame, fs)

                if tiene_voz:

                    contador_voz += 1
                    contador_silencio = 0

                    audio_frames.append(frame)

                    if contador_voz >= frames_voz:
                        hablando = True

                elif hablando:

                    contador_silencio += 1
                    audio_frames.append(frame)

                    if contador_silencio >= frames_silencio:
                        break

        if not hablando:
            print("[No se detectó voz durante el tiempo de espera]")
            return None

        audio_completo = b"".join(audio_frames)

        wav_io = io.BytesIO()

        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(audio_completo)

        wav_io.seek(0)

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)

            texto = recognizer.recognize_google(
                audio,
                language="es-ES"
            )

            print(f"Tú: {texto}")
            return texto

    except sr.UnknownValueError:
        print("[No pude entender lo que dijiste]")
        return ""

    except sr.RequestError as e:
        print(f"[Error en Google Speech Recognition: {e}]")
        return ""

    except Exception as e:
        print(f"[Error al capturar audio: {e}]")
        return ""

    

# 4. Bucle principal con conversación continua

hablar("Sistemas listos. Llámame cuando me necesites.")

while True:

    # Esperar la palabra clave para activar Hinata
    if esperar_palabra_clave():

        with cola_audio.mutex:
            cola_audio.queue.clear()

        hablar("¿Sí? Te escucho.")

        # Entrar en modo conversación
        intentos_sin_respuesta = 0

        
    while True:

        # Esperar una instrucción durante un máximo de 20 segundos
        orden = grabar_orden_segura(duracion=20)

        # Si no se detectó voz durante los 20 segundos
        if orden is None:

            hablar("Han pasado 20 segundos sin recibir instrucciones. Vuelvo al modo de espera.")
            break

        # Si se detectó voz, pero no se pudo reconocer
        if not orden:
            hablar("No he conseguido entenderte. Puedes repetirlo.")
            continue

        # Normalizar la orden
        orden_limpia = orden.lower().strip()

        # Comprobar si el usuario quiere finalizar la conversación
        palabras_salida = [
            "apágate",
            "apagate",
            "descansa",
            "adiós",
            "adios",
            "hasta luego",
            "terminar conversación",
            "terminar conversacion"
        ]

        if orden_limpia in palabras_salida:
            hablar("Entendido. Vuelvo al modo de espera. Hasta luego.")
            break

        # Procesar la orden con Ollama
        respuesta_ia = procesar_orden(orden)

        # Responder sin abandonar el modo conversación
        hablar(respuesta_ia)

    # Al terminar la conversación, volverá a esperar la palabra clave

