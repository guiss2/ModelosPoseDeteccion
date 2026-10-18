import cv2
import mediapipe as mp
import numpy as np
from alertas_sonoras import AlertaSonora

mp_pose = mp.solutions.pose  # Define los puntos corporales disponibles.
mp_drawing = mp.solutions.drawing_utils  # Dibuja la guía del esqueleto.

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
                    diferencia_altura_pies = tobillo_izq[1] - tobillo_der[1]

                    if diferencia_altura_pies < -0.05:
                        angulo_soporte = calcular_angulo(cadera_der, rodilla_der, tobillo_der)
                        modo_texto = f"Soporte: DERECHA | Angulo: {angulo_soporte:.1f}"
                    elif diferencia_altura_pies > 0.05:
                        angulo_soporte = calcular_angulo(cadera_izq, rodilla_izq, tobillo_izq)
                        modo_texto = f"Soporte: IZQUIERDA | Angulo: {angulo_soporte:.1f}"
                    else:
                        modo_texto = "Eleve un pie para iniciar"
                        alerta_sonora.emitir()
                    color_estado = (0, 255, 0) if abs(diferencia_altura_pies) > 0.05 else (0, 165, 255)
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
        pose.close()  # Libera MediaPipe incluso si ocurre un error.
        cap.release()  # Libera la cámara.
        cv2.destroyAllWindows()  # Cierra las ventanas.

if __name__ == "__main__":
    ejecutar_apoyo_unipodal()  # Ejecuta el ejercicio al abrir este archivo.