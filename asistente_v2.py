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

8. Cuando el usuario solicite modificar un recuerdo, primero consulta los recuerdos para identificar el ID correcto. Después utiliza actualizar_recuerdo con ese ID y el nuevo contenido.

9. Cuando el usuario solicite eliminar un recuerdo, primero consulta los recuerdos para identificar el ID correcto.

10. Si existen varios recuerdos que podrían corresponder a lo que quiere eliminar, pregunta al usuario cuál desea borrar antes de utilizar eliminar_recuerdo.

11. Nunca inventes IDs de recuerdos ni modifiques o elimines información sin identificar correctamente el recuerdo.

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

        # Si no necesita más herramientas, devuelve la respuesta.
        if not llamadas:
            return respuesta['message']['content']

        mensajes.append(respuesta['message'])

        # Ejecutar las herramientas solicitadas.
        for llamada in llamadas:

            nombre_funcion = llamada['function']['name']
            argumentos = llamada['function']['arguments']

            print(f"[Ejecutando: {nombre_funcion} -> {argumentos}]")

            funcion_real = mapa_funciones[nombre_funcion]
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

