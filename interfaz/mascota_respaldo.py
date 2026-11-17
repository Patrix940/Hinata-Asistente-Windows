import threading
import sys
import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QMenu
)


# Ruta de los recursos visuales
CARPETA_RECURSOS = os.path.join(
    os.path.dirname(__file__),
    "recursos"
)

IMAGEN_HINATA = os.path.join(
    CARPETA_RECURSOS,
    "hinata.png"
)

# Señal compartida para detener el asistente
evento_detencion = threading.Event()

class TrabajadorHinata(QThread):

    estado_cambiado = Signal(str)

    def run(self):

        import sys
        import os

        sys.path.append(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        import asistente_v2

        # Conectar la señal de detención de la mascota
        asistente_v2.detener_asistente = evento_detencion

        asistente_v2.cambiar_estado_callback = (
            self.estado_cambiado.emit
        )

        asistente_v2.ejecutar_asistente()


class MascotaHinata(QWidget):

    def __init__(self):
        super().__init__()

        self.posicion_anterior = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setFixedSize(230, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Espacio donde aparecerá el personaje
        self.personaje = QLabel()
        self.personaje.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.cargar_imagen()

        # Nombre de Hinata
        nombre = QLabel("Hinata")
        nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nombre.setStyleSheet("""
            color: #d9b3ff;
            font-size: 22px;
            font-weight: bold;
        """)

        estado = QLabel("Tu asistente personal")
        estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        estado.setStyleSheet("""
            color: white;
            font-size: 11px;
        """)

        layout.addWidget(self.personaje, 1)
        layout.addWidget(nombre)
        layout.addWidget(estado)

        pantalla = QApplication.primaryScreen().availableGeometry()

        self.move(
            pantalla.right() - self.width() - 30,
            pantalla.bottom() - self.height() - 30
        )

        # Conectar el cerebro con la apariencia de Hinata
        self.trabajador = TrabajadorHinata()

        self.trabajador.estado_cambiado.connect(
            self.cambiar_estado
        )

        # Iniciar el cerebro de Hinata en segundo plano
        self.trabajador.start()

    
    def cargar_imagen(self, archivo="hinata.png"):

        ruta_imagen = os.path.join(
            CARPETA_RECURSOS,
            archivo
        )

        if os.path.exists(ruta_imagen):

            imagen = QPixmap(ruta_imagen)

            if not imagen.isNull():

                imagen = imagen.scaled(
                    210,
                    280,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                self.personaje.setPixmap(imagen)
                return

        # Apariencia provisional si no existe la imagen
        self.personaje.setPixmap(QPixmap())
        self.personaje.setText("🌙")
        self.personaje.setStyleSheet("font-size: 90px;")


    def cambiar_estado(self, estado):

        imagenes = {
            "disponible": "hinata.png",
            "escuchando": "hinata.png",
            "pensando": "hinata.png",
            "hablando": "hinata.png"
        }

        archivo = imagenes.get(estado, "hinata.png")

        self.cargar_imagen(archivo)

    def closeEvent(self, event):

        # Avisar al cerebro que debe detenerse
        evento_detencion.set()

        # Esperar a que el asistente termine de forma segura
        if self.trabajador.isRunning():
            self.trabajador.wait()

        event.accept()


    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            self.posicion_anterior = (
                event.globalPosition().toPoint()
            )

    def mouseMoveEvent(self, event):

        if self.posicion_anterior is not None:

            nueva_posicion = event.globalPosition().toPoint()

            diferencia = nueva_posicion - self.posicion_anterior

            self.move(self.pos() + diferencia)

            self.posicion_anterior = nueva_posicion

    def mouseReleaseEvent(self, event):

        self.posicion_anterior = None

    def contextMenuEvent(self, event):

        menu = QMenu(self)

        ocultar = menu.addAction("Ocultar Hinata")
        salir = menu.addAction("Cerrar Hinata")

        accion = menu.exec(event.globalPos())

        if accion == ocultar:
            self.hide()

        elif accion == salir:
            QApplication.quit()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    hinata = MascotaHinata()
    hinata.show()

    sys.exit(app.exec())
