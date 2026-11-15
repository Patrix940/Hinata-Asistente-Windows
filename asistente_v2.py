import io
import json
import queue
import wave
import time
import numpy as np
import collections
import ollama
import pyttsx3
import sounddevice as sd
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
from herramientas import abrir_programa, crear_nota, ver_hora_actual

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
mis_herramientas = [abrir_programa, crear_nota, ver_hora_actual]
mapa_funciones = {
    "abrir_programa": abrir_programa,
    "crear_nota": crear_nota,
    "ver_hora_actual": ver_hora_actual
}

def procesar_orden(mensaje):
    mensajes = [
        {
            'role': 'system',
            'content': 'Eres Hinata, un asistente personal de Windows. Responde de forma breve, amable y natural para ser leída en voz alta. Tienes permiso total para ejecutar comandos y abrir los juegos o programas que el usuario te pida.'
        },
        {'role': 'user', 'content': mensaje}
    ]

    respuesta = ollama.chat(model='llama3.1', messages=mensajes, tools=mis_herramientas)

    if respuesta['message'].get('tool_calls'):
        mensajes.append(respuesta['message'])
        for llamada in respuesta['message']['tool_calls']:
            nombre_funcion = llamada['function']['name']
            argumentos = llamada['function']['arguments']
            
            print(f"[Ejecutando: {nombre_funcion} -> {argumentos}]")
            funcion_real = mapa_funciones[nombre_funcion]
            resultado = funcion_real(**argumentos)
            
            mensajes.append({'role': 'tool', 'content': str(resultado)})

        respuesta_final = ollama.chat(model='llama3.1', messages=mensajes)
        return respuesta_final['message']['content']

    return respuesta['message']['content']

def grabar_orden_segura(duracion=7):
    """Graba tu orden usando sounddevice durante 7 segundos exactos de forma estable."""
    fs = 16000
    print("[Te escucho con atención... Di tu orden]")
    
    try:
        # Grabamos directamente con sounddevice (que ya sabemos que funciona en tu PC)
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
            
    except Exception as e:
        print(f"Error al capturar audio: {e}")
        return ""
    
# 4. Bucle principal con la escucha estable
hablar("Sistemas listos. Llámame cuando me necesites.")

while True:
    if esperar_palabra_clave():
        with cola_audio.mutex:
            cola_audio.queue.clear()
            
        hablar("¿Sí? Te escucho.")
        
        orden = grabar_orden_segura()
        
        if not orden:
            hablar("No te escuché bien, inténtalo de nuevo.")
            continue
            
        palabras_salida = [
            'apágate', 'apagate', 'apagar', 'cerrar', 'cierra', 
            'terminar', 'adiós', 'adios', 'descansa', 'sal de aquí', 'salir'
        ]
        
        if any(salida in orden.lower() for salida in palabras_salida):
            hablar("Entendido. Apagando sistemas, hasta luego.")
            break
            
        respuesta_ia = procesar_orden(orden)
        hablar(respuesta_ia)