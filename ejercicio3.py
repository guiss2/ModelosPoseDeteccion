import cv2
import mediapipe as mp
from alertas_sonoras import AlertaSonora

mp_pose = mp.solutions.pose  # Permite acceder a los puntos de la pose.
mp_drawing = mp.solutions.drawing_utils  # Permite dibujar la pose detectada.

def ejecutar_postura_arbol(video_source=0):
    """
    Modelo 4: Postura del Árbol Adaptada (Vrksasana modificada).
    Valida la transferencia de carga a un solo pie y la alineación vertical del tronco.
    """
    cap = cv2.VideoCapture(video_source)  # Abre la cámara o fuente de vídeo.
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")
    alerta_sonora = AlertaSonora()
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    print("Iniciando Modelo 4: Postura del Árbol Adaptada. Mantenga un soporte cercano...")

    try:
        while True:
            ret, frame = cap.read()  # Lee un fotograma.
            if not ret:
                print("No se pudo leer un fotograma de la cámara.")
                break
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convierte a RGB para MediaPipe.
            image.flags.writeable = False
            results = pose.process(image)  # Detecta la postura.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # Convierte a BGR para mostrar.
            estado_texto = "Ajuste su posicion frente a la camara"
            color_estado = (0, 165, 255)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                required = (
                    mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                    mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.RIGHT_HIP.value,
                    mp_pose.PoseLandmark.LEFT_ANKLE.value,
                    mp_pose.PoseLandmark.RIGHT_ANKLE.value,
                )
                if all(landmarks[index].visibility >= 0.5 for index in required):
                    left_shoulder, right_shoulder = landmarks[required[0]], landmarks[required[1]]
                    left_hip, right_hip = landmarks[required[2]], landmarks[required[3]]
                    left_ankle, right_ankle = landmarks[required[4]], landmarks[required[5]]
                    center_shoulders_x = (left_shoulder.x + right_shoulder.x) / 2
                    center_hips_x = (left_hip.x + right_hip.x) / 2
                    desviacion_tronco = abs(center_shoulders_x - center_hips_x) * 100
                    diferencia_pies = abs(left_ankle.y - right_ankle.y)
                    unipodal = diferencia_pies > 0.05

                    if not unipodal:
                        estado_texto = "Eleve un pie para realizar la postura"
                        color_estado = (0, 165, 255)
                    elif desviacion_tronco < 3.5:
                        estado_texto = "Alineacion correcta: mantenga el equilibrio"
                        color_estado = (0, 255, 0)
                    else:
                        estado_texto = "ALERTA: Tronco inclinado, enderecese"
                        color_estado = (0, 0, 255)
                        alerta_sonora.emitir()
                    cv2.putText(image, f"Desvio tronco: {desviacion_tronco:.1f}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                else:
                    estado_texto = "Mantenga hombros, caderas y pies visibles"

            cv2.putText(image, "Ejercicio: Postura del Arbol Adaptada", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(image, estado_texto, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_estado, 2)
            cv2.putText(image, 'Presione "q" para salir', (30, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow("Modelo 4: Postura del Arbol Adaptada", image)
            if cv2.waitKey(10) & 0xFF == ord("q"):  # q termina la prueba.
                break
    finally:
        pose.close()  # Libera los recursos de MediaPipe.
        cap.release()  # Libera la cámara.
        cv2.destroyAllWindows()  # Cierra las ventanas de OpenCV.

if __name__ == "__main__":
    ejecutar_postura_arbol()  # Ejecuta el ejercicio al iniciar el archivo.