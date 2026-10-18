import cv2
import mediapipe as mp
import math
import time
from alertas_sonoras import AlertaSonora

# Se cargan los módulos de pose y dibujo de MediaPipe una sola vez.
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
MIN_MUESTRAS_FASE = 10


def _obtener_centro_equilibrio(landmarks):
    """Obtiene el centro corporal y la escala horizontal para medir oscilación."""
    indices = (
        mp_pose.PoseLandmark.LEFT_SHOULDER.value,
        mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
        mp_pose.PoseLandmark.LEFT_HIP.value,
        mp_pose.PoseLandmark.RIGHT_HIP.value,
        mp_pose.PoseLandmark.LEFT_ANKLE.value,
        mp_pose.PoseLandmark.RIGHT_ANKLE.value,
    )
    if not all(landmarks[index].visibility >= 0.5 for index in indices):
        return None

    hombros_x = (
        landmarks[indices[0]].x + landmarks[indices[1]].x
    ) / 2
    caderas_x = (landmarks[indices[2]].x + landmarks[indices[3]].x) / 2
    tobillos_x = (landmarks[indices[4]].x + landmarks[indices[5]].x) / 2
    centro_x = (hombros_x + caderas_x + tobillos_x) / 3
    centro_y = (
        landmarks[indices[0]].y
        + landmarks[indices[1]].y
        + landmarks[indices[2]].y
        + landmarks[indices[3]].y
    ) / 4
    escala = abs(landmarks[indices[0]].x - landmarks[indices[1]].x)
    return centro_x, centro_y, escala


def evaluar_romberg(video_source=0, duracion_fase=30.0):
    """Evalúa la oscilación corporal con ojos abiertos y cerrados.

    La transición a la fase de ojos cerrados se hace con la tecla ESPACIO para
    que el programa no tenga que inferir el cierre de ojos con una cámara 2D.
    """
    if duracion_fase <= 0:
        raise ValueError("La duración de cada fase debe ser mayor que cero.")

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")

    resultados = {
        "prueba": "romberg",
        "completada": False,
        "ojos_abiertos": None,
        "ojos_cerrados": None,
        "diferencia_oscilacion": None,
        "estado": "Sin datos",
        "interpretacion": None,
    }
    fases = ("ojos_abiertos", "ojos_cerrados")
    fase = 0
    inicio_fase = None
    fase_cerrada_lista = False
    referencia = None
    oscilaciones = []
    alerta_sonora = AlertaSonora()

    try:
        with mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose:
            while fase < len(fases):
                ret, frame = cap.read()
                if not ret:
                    raise RuntimeError("No se pudo leer un fotograma de la cámara.")

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = pose.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if inicio_fase is None and fase == 0:
                    inicio_fase = time.monotonic()
                    referencia = None
                    oscilaciones = []

                centro = None
                if inicio_fase is not None and results.pose_landmarks:
                    centro = _obtener_centro_equilibrio(results.pose_landmarks.landmark)
                    mp_drawing.draw_landmarks(
                        image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                    )

                if centro is not None:
                    centro_x, centro_y, escala = centro
                    if escala > 0:
                        if referencia is None:
                            referencia = (centro_x, centro_y)
                        distancia = math.hypot(
                            centro_x - referencia[0], centro_y - referencia[1]
                        ) / escala * 100
                        oscilaciones.append(distancia)

                transcurrido = (
                    time.monotonic() - inicio_fase if inicio_fase is not None else 0
                )
                restante = max(0, duracion_fase - transcurrido)
                nombre_fase = "ojos abiertos" if fase == 0 else "ojos cerrados"
                cv2.putText(
                    image,
                    f"Romberg: {nombre_fase} ({restante:.0f}s)",
                    (30, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                if fase == 0:
                    instruccion = "Coloque los pies juntos y mantenga los ojos abiertos"
                elif not fase_cerrada_lista:
                    instruccion = "Cierre los ojos y presione ESPACIO para comenzar"
                else:
                    instruccion = "Mantenga los ojos cerrados. ESC: cancelar"
                cv2.putText(
                    image,
                    instruccion,
                    (30, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )
                cv2.imshow("Prueba de Romberg", image)
                tecla = cv2.waitKey(10) & 0xFF

                if tecla == 27:
                    break
                if fase == 1 and not fase_cerrada_lista and tecla == 32:
                    fase_cerrada_lista = True
                    inicio_fase = time.monotonic()
                    referencia = None
                    oscilaciones = []

                if inicio_fase is not None and transcurrido >= duracion_fase:
                    if len(oscilaciones) >= MIN_MUESTRAS_FASE:
                        resultados[fases[fase]] = {
                            "oscilacion_maxima": round(max(oscilaciones), 2),
                            "oscilacion_promedio": round(
                                sum(oscilaciones) / len(oscilaciones), 2
                            ),
                            "muestras": len(oscilaciones),
                        }
                    fase += 1
                    inicio_fase = None
                    fase_cerrada_lista = False

            if resultados["ojos_abiertos"] and resultados["ojos_cerrados"]:
                abiertas = resultados["ojos_abiertos"]["oscilacion_promedio"]
                cerradas = resultados["ojos_cerrados"]["oscilacion_promedio"]
                resultados["diferencia_oscilacion"] = round(cerradas - abiertas, 2)
                resultados["estado"] = (
                    "Mayor oscilación con ojos cerrados"
                    if cerradas > abiertas
                    else "Sin aumento evidente de oscilación"
                )
                resultados["interpretacion"] = (
                    "Se observó mayor oscilación al retirar la referencia visual."
                    if cerradas > abiertas
                    else "No se observó un aumento de oscilación al retirar la referencia visual."
                )
                resultados["completada"] = True
                if cerradas > abiertas:
                    alerta_sonora.emitir()
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return resultados


def mostrar_resultado_romberg(resultados):
    """Muestra en consola el resumen de una prueba completada."""
    print("\n--- Resultado de la prueba de Romberg ---")
    if not resultados["completada"]:
        print("La prueba no se completó o no hubo suficientes datos válidos.")
        return

    abiertos = resultados["ojos_abiertos"]
    cerrados = resultados["ojos_cerrados"]
    print(f"Ojos abiertos - oscilación promedio: "
          f"{abiertos['oscilacion_promedio']:.2f}%")
    print(f"Ojos cerrados - oscilación promedio: "
          f"{cerrados['oscilacion_promedio']:.2f}%")
    print(f"Diferencia: {resultados['diferencia_oscilacion']:.2f}%")
    print(f"Resultado: {resultados['estado']}")
    print(f"Interpretación: {resultados['interpretacion']}")
    print("Nota: este resultado es orientativo y no constituye un diagnóstico clínico.")


if __name__ == "__main__":
    resultado = evaluar_romberg()
    time.sleep(5)
    mostrar_resultado_romberg(resultado)
    input("\nPresione ENTER para cerrar...")