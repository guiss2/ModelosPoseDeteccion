import cv2
import mediapipe as mp
from statistics import median
import time
from alertas_sonoras import AlertaSonora

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
UMBRAL_DESVIO_LATERAL = 5.0
MUESTRAS_CALIBRACION = 30

def ejecutar_marcha_tandem(video_source=0):
    """
    Modelo 2: Marcha Tándem (Talón-Punta).
    Monitorea el desplazamiento lateral del centro de las caderas durante la
    marcha. La desviación se normaliza con el ancho de los hombros.
    """
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara o fuente de vídeo.")
    
    alerta_sonora = AlertaSonora()
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mediciones = []
    
    referencias_x = []
    centro_inicial_x = None
    print("Iniciando Modelo 2: Marcha Tandem. Manténgase estable unos segundos al iniciar...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("No se pudo leer un fotograma de la cámara.")
                break
                
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                required = (
                    mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                    mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.RIGHT_HIP.value,
                )
                
                if all(landmarks[i].visibility >= 0.5 for i in required):
                    left_shoulder = landmarks[required[0]]
                    right_shoulder = landmarks[required[1]]
                    left_hip = landmarks[required[2]]
                    right_hip = landmarks[required[3]]
                    
                    shoulder_width = abs(left_shoulder.x - right_shoulder.x)
                    centro_actual_x = (left_hip.x + right_hip.x) / 2.0

                    if shoulder_width <= 0:
                        cv2.putText(
                            image, "Mantenga los hombros visibles", (30, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2
                        )
                    elif centro_inicial_x is None:
                        referencias_x.append(centro_actual_x)
                        estado_texto = (
                            f"Calibrando... {len(referencias_x)}/"
                            f"{MUESTRAS_CALIBRACION}"
                        )
                        cv2.putText(
                            image, estado_texto, (30, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2
                        )
                        mp_drawing.draw_landmarks(
                            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                        )
                    else:
                        desvio_lateral = (
                            abs(centro_actual_x - centro_inicial_x)
                            / shoulder_width
                            * 100
                        )
                        mediciones.append(desvio_lateral)

                        if desvio_lateral > UMBRAL_DESVIO_LATERAL:
                            estado_actual = "incorrecta"
                            estado_texto = "ALERTA: Desequilibrio lateral detectado"
                            color_alerta = (0, 0, 255)
                        else:
                            estado_actual = "correcta"
                            estado_texto = "Postura estable en tandem"
                            color_alerta = (0, 255, 0)

                        alerta_sonora.anunciar_estado(estado_actual)
                        cv2.putText(
                            image, estado_texto, (30, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2
                        )
                        cv2.putText(
                            image,
                            f"Desvio lateral: {desvio_lateral:.1f}%",
                            (30, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 0),
                            2,
                        )
                        mp_drawing.draw_landmarks(
                            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                        )
                else:
                    cv2.putText(image, "Mantenga el cuerpo visible", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            else:
                cv2.putText(image, "Ajuste su posicion frente a la camara", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            cv2.putText(image, "Ejercicio: Marcha Tandem", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("Modelo 2: Marcha Tandem (Talon-Punta)", image)
            
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break
            if centro_inicial_x is None and len(referencias_x) >= MUESTRAS_CALIBRACION:
                centro_inicial_x = median(referencias_x)
                estado_texto = "Calibración completada"
    finally:
        pose.close()
        cap.release()
        cv2.destroyAllWindows()

    if not mediciones:
        return {
            "prueba": "marcha_tandem",
            "completada": False,
            "muestras": 0,
            "desvio_promedio": None,
            "desvio_maximo": None,
            "estado": "Sin datos",
            "interpretacion": "No se obtuvieron suficientes datos válidos.",
        }

    desvio_promedio = sum(mediciones) / len(mediciones)
    desvio_maximo = max(mediciones)
    estado = (
        "Desequilibrio lateral detectado"
        if desvio_promedio > UMBRAL_DESVIO_LATERAL
        else "Postura estable en tandem"
    )
    return {
        "prueba": "marcha_tandem",
        "completada": True,
        "muestras": len(mediciones),
        "desvio_promedio": round(desvio_promedio, 2),
        "desvio_maximo": round(desvio_maximo, 2),
        "estado": estado,
        "interpretacion": (
            f"El desvío lateral promedio supera el umbral técnico de "
            f"{UMBRAL_DESVIO_LATERAL:.1f}%."
            if desvio_promedio > UMBRAL_DESVIO_LATERAL
            else f"El desvío lateral promedio se mantiene dentro del umbral "
            f"técnico de {UMBRAL_DESVIO_LATERAL:.1f}%."
        ),
    }

def mostrar_resultado_marcha_tandem(resultado):
    print("\n--- Resultado de la marcha tándem ---")
    if not resultado["completada"]:
        print("La prueba no se completó o no hubo suficientes datos válidos.")
        return
    print(f"Desvío promedio: {resultado['desvio_promedio']}")
    print(f"Desvío máximo: {resultado['desvio_maximo']}")
    print(f"Muestras válidas: {resultado['muestras']}")
    print(f"Resultado: {resultado['estado']}")
    print(f"Interpretación: {resultado['interpretacion']}")
    print("Nota: este resultado es orientativo y no constituye un diagnóstico clínico.")

if __name__ == "__main__":
    resultado = ejecutar_marcha_tandem()
    time.sleep(2)
    mostrar_resultado_marcha_tandem(resultado)
    input("\nPresione ENTER para cerrar...")