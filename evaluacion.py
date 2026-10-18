import cv2
import mediapipe as mp
from alertas_sonoras import AlertaSonora

# Se cargan los módulos de pose y dibujo de MediaPipe una sola vez.
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


def evaluar_postura_estatica(video_source=0):
    """
    Modelo 1: Evalúa la alineación vertical y simetría corporal (Hombros y Tronco).
    Retorna métricas de desviación para guardar en la base de datos como línea base.
    """
    cap = cv2.VideoCapture(video_source)  # Abre la cámara o fuente de vídeo.
    if not cap.isOpened():  # Evita iniciar el análisis si la cámara no está disponible.
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")

    alerta_sonora = AlertaSonora()  # Controla las alertas sin emitir un pitido por cada fotograma.
    resultados_sesion = {
        "hombro_desnivel": None,
        "inclinacion_tronco": None,
        "estado": "Sin datos",
    }  # Conserva el último resultado válido de la sesión.

    try:
        with mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose:  # Crea el detector y garantiza su liberación.
            print("Iniciando evaluación postural inicial. Manténgase de pie frente a la cámara...")

            while True:
                ret, frame = cap.read()  # Lee un fotograma de la cámara.
                if not ret:
                    print("No se pudo leer un fotograma de la cámara.")
                    break

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # MediaPipe requiere formato RGB.
                image.flags.writeable = False  # Evita una copia innecesaria durante el procesamiento.
                results = pose.process(image)  # Obtiene los puntos corporales.
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # OpenCV muestra imágenes BGR.

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    indices = (
                        mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                        mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                        mp_pose.PoseLandmark.LEFT_HIP.value,
                        mp_pose.PoseLandmark.RIGHT_HIP.value,
                    )
                    if all(landmarks[index].visibility >= 0.5 for index in indices):
                        hombro_izq = landmarks[indices[0]]
                        hombro_der = landmarks[indices[1]]
                        cadera_izq = landmarks[indices[2]]
                        cadera_der = landmarks[indices[3]]

                        desnivel_hombros = abs(hombro_izq.y - hombro_der.y) * 100
                        centro_hombros_x = (hombro_izq.x + hombro_der.x) / 2
                        centro_caderas_x = (cadera_izq.x + cadera_der.x) / 2
                        inclinacion_tronco = abs(centro_hombros_x - centro_caderas_x) * 100
                        resultados_sesion.update(
                            hombro_desnivel=round(desnivel_hombros, 2),
                            inclinacion_tronco=round(inclinacion_tronco, 2),
                            estado="Correcta" if desnivel_hombros < 3.0 else "Revisar",
                        )

                        color = (0, 255, 0) if desnivel_hombros < 3.0 else (0, 0, 255)
                        if desnivel_hombros >= 3.0:
                            alerta_sonora.emitir()
                        cv2.putText(
                            image,
                            f"Desnivel hombros: {desnivel_hombros:.1f}%",
                            (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            color,
                            2,
                        )
                        cv2.putText(
                            image,
                            f"Inclinacion tronco: {inclinacion_tronco:.1f}%",
                            (30, 85),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            color,
                            2,
                        )
                        mp_drawing.draw_landmarks(
                            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                        )
                    else:
                        cv2.putText(
                            image,
                            "Mantenga hombros y caderas visibles",
                            (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 165, 255),
                            2,
                        )

                cv2.putText(
                    image,
                    'Presione "ESC" para guardar evaluacion',
                    (30, 450),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )
                cv2.imshow("Modelo 1: Evaluacion Postural Inicial", image)
                if cv2.waitKey(10) & 0xFF == 27:  # ESC finaliza y conserva el último dato válido.
                    break
    finally:
        cap.release()  # Libera la cámara aunque ocurra un error.
        cv2.destroyAllWindows()  # Cierra las ventanas creadas por OpenCV.

    return resultados_sesion

if __name__ == "__main__":
    evaluar_postura_estatica()  # Ejecuta la evaluación cuando se inicia este archivo directamente.