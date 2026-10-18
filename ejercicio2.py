import cv2
import mediapipe as mp
import numpy as np
import time
from alertas_sonoras import AlertaSonora

mp_pose = mp.solutions.pose  # Define los puntos corporales disponibles.
mp_drawing = mp.solutions.drawing_utils  # Dibuja la guía del esqueleto.
UMBRAL_DIFERENCIA_PIES = 0.05
MIN_MUESTRAS_VALIDAS = 10

def calcular_angulo(punto1, punto2, punto3):
    """Calcula el ángulo en punto2 formado por los otros dos puntos."""
    a = np.array(punto1)
    b = np.array(punto2)
    c = np.array(punto3)
    
    radianes = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angulo = np.abs(radianes * 180.0 / np.pi)
    if angulo > 180.0:
        angulo = 360 - angulo
    return angulo

def ejecutar_apoyo_unipodal(video_source=0):
    """
    Modelo 3: Apoyo Unipodal Intercalado.
    Detecta la elevación de una pierna y evalúa la estabilidad del miembro de soporte.
    """
    cap = cv2.VideoCapture(video_source)  # Abre la cámara o el vídeo indicado.
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")
    
    alerta_sonora = AlertaSonora()
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    angulos_soporte = []
    diferencias_pies = []
    soportes_detectados = {"izquierda": 0, "derecha": 0}
    muestras_postura_valida = 0
    muestras_evaluables = 0
    
    print("Iniciando Modelo 3: Apoyo Unipodal Intercalado. Prepárese frente a la cámara...")

    try:
        while True:
            ret, frame = cap.read()  # Lee un fotograma.
            if not ret:
                print("No se pudo leer un fotograma de la cámara.")
                break
                
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Prepara la imagen para MediaPipe.
            image.flags.writeable = False
            results = pose.process(image)  # Detecta la postura.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # Prepara la imagen para OpenCV.
            
            modo_texto = "No se detecta el cuerpo"
            color_estado = (0, 165, 255)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                required = (
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.LEFT_KNEE.value,
                    mp_pose.PoseLandmark.LEFT_ANKLE.value,
                    mp_pose.PoseLandmark.RIGHT_HIP.value,
                    mp_pose.PoseLandmark.RIGHT_KNEE.value,
                    mp_pose.PoseLandmark.RIGHT_ANKLE.value,
                )
                
                if all(landmarks[index].visibility >= 0.5 for index in required):
                    cadera_izq = [landmarks[required[0]].x, landmarks[required[0]].y]
                    rodilla_izq = [landmarks[required[1]].x, landmarks[required[1]].y]
                    tobillo_izq = [landmarks[required[2]].x, landmarks[required[2]].y]
                    cadera_der = [landmarks[required[3]].x, landmarks[required[3]].y]
                    rodilla_der = [landmarks[required[4]].x, landmarks[required[4]].y]
                    tobillo_der = [landmarks[required[5]].x, landmarks[required[5]].y]
                    
                    escala_piernas = (
                        abs(cadera_izq[1] - tobillo_izq[1])
                        + abs(cadera_der[1] - tobillo_der[1])
                    ) / 2
                    if escala_piernas <= 0:
                        modo_texto = "Mantenga las piernas visibles"
                    else:
                        diferencia_altura_pies = (
                            tobillo_izq[1] - tobillo_der[1]
                        ) / escala_piernas
                        muestras_evaluables += 1

                        if diferencia_altura_pies < -UMBRAL_DIFERENCIA_PIES:
                            angulo_soporte = calcular_angulo(
                                cadera_der, rodilla_der, tobillo_der
                            )
                            angulos_soporte.append(angulo_soporte)
                            diferencias_pies.append(abs(diferencia_altura_pies))
                            soportes_detectados["derecha"] += 1
                            muestras_postura_valida += 1
                            modo_texto = (
                                f"Soporte: DERECHA | Angulo: {angulo_soporte:.1f}"
                            )
                        elif diferencia_altura_pies > UMBRAL_DIFERENCIA_PIES:
                            angulo_soporte = calcular_angulo(
                                cadera_izq, rodilla_izq, tobillo_izq
                            )
                            angulos_soporte.append(angulo_soporte)
                            diferencias_pies.append(abs(diferencia_altura_pies))
                            soportes_detectados["izquierda"] += 1
                            muestras_postura_valida += 1
                            modo_texto = (
                                f"Soporte: IZQUIERDA | Angulo: {angulo_soporte:.1f}"
                            )
                        else:
                            modo_texto = "Eleve un pie para iniciar"

                        color_estado = (
                            (0, 255, 0)
                            if abs(diferencia_altura_pies) > UMBRAL_DIFERENCIA_PIES
                            else (0, 165, 255)
                        )
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                else:
                    modo_texto = "Mantenga caderas, rodillas y tobillos visibles"

            cv2.putText(image, "Ejercicio: Apoyo Unipodal", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(image, modo_texto, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_estado, 2)
            cv2.putText(image, 'Presione "q" para salir', (30, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow("Modelo 3: Apoyo Unipodal Intercalado", image)
            
            if cv2.waitKey(10) & 0xFF == ord("q"):  # q termina la prueba.
                break
    finally:
        pose.close()  # Libera MediaPipe.
        cap.release()  # Libera la cámara.
        cv2.destroyAllWindows()  # Cierra las ventanas.

    if len(angulos_soporte) < MIN_MUESTRAS_VALIDAS:
        return {
            "prueba": "apoyo_unipodal",
            "completada": False,
            "muestras": 0,
            "angulo_promedio": None,
            "angulo_maximo": None,
            "diferencia_pies_promedio": None,
            "porcentaje_apoyo_unipodal": 0.0,
            "pierna_soporte_predominante": None,
            "estado": "Sin datos",
            "interpretacion": (
                "No se obtuvieron suficientes muestras de apoyo unipodal "
                f"(mínimo: {MIN_MUESTRAS_VALIDAS})."
            ),
        }

    angulo_promedio = sum(angulos_soporte) / len(angulos_soporte)
    pierna_soporte = max(soportes_detectados, key=soportes_detectados.get)
    porcentaje_apoyo = (
        muestras_postura_valida / muestras_evaluables * 100
        if muestras_evaluables
        else 0.0
    )
    return {
        "prueba": "apoyo_unipodal",
        "completada": True,
        "muestras": len(angulos_soporte),
        "angulo_promedio": round(angulo_promedio, 2),
        "angulo_maximo": round(max(angulos_soporte), 2),
        "diferencia_pies_promedio": round(
            sum(diferencias_pies) / len(diferencias_pies), 4
        ),
        "porcentaje_apoyo_unipodal": round(porcentaje_apoyo, 2),
        "pierna_soporte_predominante": pierna_soporte,
        "estado": "Apoyo unipodal detectado",
        "interpretacion": (
            f"Se detectó principalmente apoyo sobre la pierna {pierna_soporte}."
        ),
    }


def mostrar_resultado_apoyo_unipodal(resultado):
    """Muestra en consola el resumen del apoyo unipodal."""
    print("\n--- Resultado del apoyo unipodal ---")
    if not resultado["completada"]:
        print("La prueba no se completó o no hubo suficientes datos válidos.")
        return
    print(f"Ángulo promedio de soporte: {resultado['angulo_promedio']:.2f}°")
    print(f"Ángulo máximo de soporte: {resultado['angulo_maximo']:.2f}°")
    print(f"Diferencia normalizada promedio de pies: "
          f"{resultado['diferencia_pies_promedio']:.4f}")
    print(f"Pierna de soporte predominante: "
          f"{resultado['pierna_soporte_predominante']}")
    print(f"Porcentaje de apoyo unipodal: "
          f"{resultado['porcentaje_apoyo_unipodal']:.2f}%")
    print(f"Muestras válidas: {resultado['muestras']}")
    print(f"Resultado: {resultado['estado']}")
    print(f"Interpretación: {resultado['interpretacion']}")
    print("Nota: este resultado es orientativo y no constituye un diagnóstico clínico.")


if __name__ == "__main__":
    resultado = ejecutar_apoyo_unipodal()
    time.sleep(2)
    mostrar_resultado_apoyo_unipodal(resultado)
    input("\nPresione ENTER para cerrar...")