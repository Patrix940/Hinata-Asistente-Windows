import os
import subprocess
from datetime import datetime

def abrir_programa(nombre: str) -> str:
    """Abre un programa básico de Windows. Opciones válidas: calculadora, bloc, navegador."""
    programas = {
        "calculadora": "calc.exe",
        "bloc": "notepad.exe",
        "navegador": "start brave",
        "steam": 'start "" "C:\\Program Files (x86)\\Steam\\steam.exe"',
        "epic": 'start "" "C:\\Program Files (x86)\\Epic Games\\Launcher\\Portal\\Binaries\\Win32\\EpicGamesLauncher.exe"',
        "valorant": 'start "" "C:\\Riot Games\\Riot Client\\RiotClientServices.exe" --launch-product=valorant --launch-patchline=live',
        "league of legends": 'start "" "C:\\Riot Games\\Riot Client\\RiotClientServices.exe" --launch-product=league_of_legends --launch-patchline=live',
        "roblox": 'start "" "C:\\Users\\el_mo\\AppData\\Local\\Roblox\\Versions\\version-4ea8e85481e34f46\\RobloxPlayerBeta.exe"',
        "discord": 'start "" "C:\\Users\\el_mo\\AppData\\Local\\Discord\\Discord.exe"',
        "spotify": 'explorer.exe shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify'
    }
    comando = programas.get(nombre.lower())
    if comando:
        subprocess.Popen(comando, shell=True)
        return f"Se abrió {nombre} correctamente."
    return f"No tengo configurado el programa '{nombre}'."

def crear_nota(titulo: str, contenido: str) -> str:
    """Crea un archivo de texto (.txt) en el Escritorio de Windows."""
    escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    ruta_archivo = os.path.join(escritorio, f"{titulo}.txt")
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    return f"Nota '{titulo}.txt' guardada en el Escritorio."

def ver_hora_actual() -> str:
    """Devuelve la fecha y hora actual del sistema."""
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"La fecha y hora actual es {ahora}."