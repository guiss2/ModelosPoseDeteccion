import cv2
import mediapipe as mp
import numpy as np
import time
from alertas_sonoras import AlertaSonora

mp_pose = mp.solutions.pose  # Permite acceder a los puntos de la pose.
mp_drawing = mp.solutions.drawing_utils  # Permite dibujar la pose detectada.
UMBRAL_DESVIO_TRONCO = 3.5
UMBRAL_PIE_PANTORRILLA = 0.45
UMBRAL_APERTURA_RODILLA = 0.08
MIN_MUESTRAS_VALIDAS = 10


def calcular_angulo(punto1, punto2, punto3):
    """Calcula el ángulo formado en punto2 por punto1 y punto3."""
    a = np.array(punto1, dtype=float)
    b = np.array(punto2, dtype=float)
    c = np.array(punto3, dtype=float)
    primer_vector = a - b
    segundo_vector = c - b
    denominador = np.linalg.norm(primer_vector) * np.linalg.norm(segundo_vector)
    if denominador == 0:
        return 0.0
    coseno = np.clip(np.dot(primer_vector, segundo_vector) / denominador, -1.0, 1.0)
    return float(np.degrees(np.arccos(coseno)))


def punto_distancia(punto1, punto2):
    """Devuelve la distancia entre dos puntos normalizados de MediaPipe."""
    return float(np.linalg.norm(np.array(punto1) - np.array(punto2)))


def ejecutar_postura_arbol(video_source=0):
    """
    Modelo 4: Postura del Árbol Adaptada (Vrksasana modificada).
    Valida la silueta de árbol con o sin apoyo opcional en una silla.

    La silla no se detecta como objeto porque la cámara puede no mostrarla
    completa; se permite como apoyo de seguridad, pero no cambia la evaluación.
    """
    cap = cv2.VideoCapture(video_source)  # Abre la cámara o fuente de vídeo.
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")
    
    alerta_sonora = AlertaSonora()
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    desviaciones_tronco = []
    posturas_correctas = 0
    
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
                    mp_pose.PoseLandmark.LEFT_KNEE.value,
                    mp_pose.PoseLandmark.RIGHT_KNEE.value,
                    mp_pose.PoseLandmark.LEFT_ANKLE.value,
                    mp_pose.PoseLandmark.RIGHT_ANKLE.value,
                    mp_pose.PoseLandmark.LEFT_WRIST.value,
                    mp_pose.PoseLandmark.RIGHT_WRIST.value,
                )
                if all(landmarks[index].visibility >= 0.5 for index in required):
                    left_shoulder, right_shoulder = landmarks[required[0]], landmarks[required[1]]
                    left_hip, right_hip = landmarks[required[2]], landmarks[required[3]]
                    left_knee, right_knee = landmarks[required[4]], landmarks[required[5]]
                    left_ankle, right_ankle = landmarks[required[6]], landmarks[required[7]]
                    left_wrist, right_wrist = landmarks[required[8]], landmarks[required[9]]
                    
                    center_shoulders_x = (left_shoulder.x + right_shoulder.x) / 2
                    center_hips_x = (left_hip.x + right_hip.x) / 2
                    shoulder_width = max(
                        abs(left_shoulder.x - right_shoulder.x), 1e-6
                    )
                    desviacion_tronco = (
                        abs(center_shoulders_x - center_hips_x)
                        / shoulder_width
                        * 100
                    )
                    desviaciones_tronco.append(desviacion_tronco)
                    
                    left_leg_angle = calcular_angulo(
                        (left_hip.x, left_hip.y),
                        (left_knee.x, left_knee.y),
                        (left_ankle.x, left_ankle.y),
                    )
                    right_leg_angle = calcular_angulo(
                        (right_hip.x, right_hip.y),
                        (right_knee.x, right_knee.y),
                        (right_ankle.x, right_ankle.y),
                    )
                    
                    left_leg_length = punto_distancia(
                        (left_hip.x, left_hip.y),
                        (left_ankle.x, left_ankle.y),
                    )
                    right_leg_length = punto_distancia(
                        (right_hip.x, right_hip.y),
                        (right_ankle.x, right_ankle.y),
                    )
                    left_foot_near_right_calf = (
                        punto_distancia(
                            (left_ankle.x, left_ankle.y),
                            (right_knee.x, right_knee.y),
                        )
                        < right_leg_length * UMBRAL_PIE_PANTORRILLA
                    )
                    right_foot_near_left_calf = (
                        punto_distancia(
                            (right_ankle.x, right_ankle.y),
                            (left_knee.x, left_knee.y),
                        )
                        < left_leg_length * UMBRAL_PIE_PANTORRILLA
                    )
                    
                    left_knee_open = (
                        left_knee.x
                        < left_hip.x - shoulder_width * UMBRAL_APERTURA_RODILLA
                    )
                    right_knee_open = (
                        right_knee.x
                        > right_hip.x + shoulder_width * UMBRAL_APERTURA_RODILLA
                    )
                    left_tree_side = (
                        left_foot_near_right_calf
                        and left_knee_open
                        and 20.0 <= left_leg_angle <= 150.0
                    )
                    right_tree_side = (
                        right_foot_near_left_calf
                        and right_knee_open
                        and 20.0 <= right_leg_angle <= 150.0
                    )
                    
                    hands_in_prayer = (
                        punto_distancia(
                            (left_wrist.x, left_wrist.y),
                            (right_wrist.x, right_wrist.y),
                        )
                        < 0.18
                        and left_wrist.y < left_hip.y
                        and right_wrist.y < right_hip.y
                    )
                    
                    tree_silhouette = left_tree_side or right_tree_side
                    
                    postura_correcta = (
                        tree_silhouette
                        and desviacion_tronco < UMBRAL_DESVIO_TRONCO
                    )
                    if postura_correcta:
                        posturas_correctas += 1

                    if not tree_silhouette:
                        estado_texto = "Eleve el pie hacia la pantorrilla y abra la rodilla"
                        color_estado = (0, 165, 255)
                    elif desviacion_tronco < UMBRAL_DESVIO_TRONCO:
                        if hands_in_prayer:
                            estado_texto = "Arbol correcto: manos en posicion de yoga"
                        else:
                            estado_texto = "Arbol correcto: puede usar silla o apoyar una mano"
                        color_estado = (0, 255, 0)
                    else:
                        estado_texto = "ALERTA: Tronco inclinado, enderecese"
                        color_estado = (0, 0, 255)
                        alerta_sonora.emitir()
                            
                    cv2.putText(
                        image,
                        f"Desvio tronco: {desviacion_tronco:.1f}",
                        (30, 120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 0),
                        2,
                    )
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                else:
                    estado_texto = "Mantenga hombros, caderas, piernas y manos visibles"

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

    if len(desviaciones_tronco) < MIN_MUESTRAS_VALIDAS:
        return {
            "prueba": "postura_arbol",
            "completada": False,
            "muestras": 0,
            "desvio_tronco_promedio": None,
            "desvio_tronco_maximo": None,
            "porcentaje_posturas_correctas": None,
            "estado": "Sin datos",
            "interpretacion": (
                "No se obtuvieron suficientes muestras de postura "
                f"(mínimo: {MIN_MUESTRAS_VALIDAS})."
            ),
        }

    desvio_promedio = sum(desviaciones_tronco) / len(desviaciones_tronco)
    porcentaje_correctas = posturas_correctas / len(desviaciones_tronco) * 100
    estado = (
        "Postura del árbol correcta"
        if porcentaje_correctas > 0
        else "Postura del árbol por corregir"
    )
    return {
        "prueba": "postura_arbol",
        "completada": True,
        "muestras": len(desviaciones_tronco),
        "desvio_tronco_promedio": round(desvio_promedio, 2),
        "desvio_tronco_maximo": round(max(desviaciones_tronco), 2),
        "porcentaje_posturas_correctas": round(porcentaje_correctas, 2),
        "estado": estado,
        "interpretacion": (
            "La postura cumplió la silueta y el umbral de desviación en parte de la sesión."
            if porcentaje_correctas > 0
            else "No se detectó una postura del árbol válida durante la sesión."
        ),
    }


def mostrar_resultado_postura_arbol(resultado):
    """Muestra en consola el resumen de la postura del árbol."""
    print("\n--- Resultado de la postura del árbol ---")
    if not resultado["completada"]:
        print("La prueba no se completó o no hubo suficientes datos válidos.")
        return
    print(f"Desvío de tronco promedio: {resultado['desvio_tronco_promedio']:.2f}")
    print(f"Desvío de tronco máximo: {resultado['desvio_tronco_maximo']:.2f}")
    print(f"Posturas correctas: {resultado['porcentaje_posturas_correctas']:.2f}%")
    print(f"Muestras válidas: {resultado['muestras']}")
    print(f"Resultado: {resultado['estado']}")
    print(f"Interpretación: {resultado['interpretacion']}")
    print("Nota: este resultado es orientativo y no constituye un diagnóstico clínico.")


if __name__ == "__main__":
    resultado = ejecutar_postura_arbol()
    time.sleep(2)
    mostrar_resultado_postura_arbol(resultado)
    input("\nPresione ENTER para cerrar...")