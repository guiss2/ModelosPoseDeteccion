import cv2
import mediapipe as mp
from alertas_sonoras import AlertaSonora

mp_pose = mp.solutions.pose  # Acceso a los puntos corporales de MediaPipe.
mp_drawing = mp.solutions.drawing_utils  # Herramientas para dibujar el esqueleto.

def ejecutar_marcha_tandem(video_source=0):
    """
    Modelo 2: Marcha Tándem (Talón-Punta).
    Monitorea la alineación horizontal de los hombros y caderas para detectar 
    desequilibrios laterales durante la caminata en línea recta.
    """
    cap = cv2.VideoCapture(video_source)  # Abre la fuente de vídeo.
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")
    alerta_sonora = AlertaSonora()  # Evita repetir alertas continuamente.
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    print("Iniciando Modelo 2: Marcha Tandem. Colóquese de frente a la cámara...")

    try:
        while True:
            ret, frame = cap.read()  # Lee un fotograma.
            if not ret:
                print("No se pudo leer un fotograma de la cámara.")
                break
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convierte BGR a RGB para MediaPipe.
            image.flags.writeable = False
            results = pose.process(image)  # Detecta la pose.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # Convierte de vuelta para mostrar.

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                required = (
                    mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                    mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.RIGHT_HIP.value,
                )
                if all(landmarks[index].visibility >= 0.5 for index in required):
                    shoulder_width = abs(
                        landmarks[required[0]].x - landmarks[required[1]].x
                    )
                    hip_width = abs(
                        landmarks[required[2]].x - landmarks[required[3]].x
                    )
                    desequilibrio_lateral = abs(shoulder_width - hip_width) * 100
                    if desequilibrio_lateral > 5.0:
                        estado_actual = "incorrecta"
                        estado_texto = "ALERTA: Desequilibrio lateral detectado"
                        color_alerta = (0, 0, 255)
                    else:
                        estado_actual = "correcta"
                        estado_texto = "Postura estable en tandem"
                        color_alerta = (0, 255, 0)
                    alerta_sonora.anunciar_estado(estado_actual)
                    cv2.putText(image, estado_texto, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2)
                    cv2.putText(image, f"Desvio: {desequilibrio_lateral:.1f}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                else:
                    cv2.putText(image, "Mantenga hombros y caderas visibles", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            else:
                cv2.putText(image, "Ajuste su posicion frente a la camara", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            cv2.putText(image, "Ejercicio: Marcha Tandem", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("Modelo 2: Marcha Tandem (Talon-Punta)", image)
            if cv2.waitKey(10) & 0xFF == ord("q"):  # La tecla q finaliza el ejercicio.
                break
    finally:
        pose.close()  # Libera los recursos de MediaPipe.
        cap.release()  # Libera la cámara.
        cv2.destroyAllWindows()  # Cierra las ventanas.

if __name__ == "__main__":
    ejecutar_marcha_tandem()  # Ejecuta la marcha al iniciar el archivo.