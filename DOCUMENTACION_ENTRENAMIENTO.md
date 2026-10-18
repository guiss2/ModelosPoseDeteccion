# Documentación para el entrenamiento de los modelos

## 1. Situación actual del proyecto

El proyecto utiliza **MediaPipe Pose** para detectar puntos de referencia del cuerpo humano a partir de la cámara. Entre los puntos detectados se encuentran:

- Nariz.
- Hombros izquierdo y derecho.
- Caderas izquierda y derecha.
- Rodillas izquierda y derecha.
- Tobillos izquierdo y derecho.

MediaPipe Pose es un modelo previamente entrenado. Por lo tanto, en el estado actual del proyecto **no se está entrenando un modelo de inteligencia artificial propio**. El programa utiliza MediaPipe para obtener coordenadas corporales y, posteriormente, aplica reglas y umbrales definidos manualmente.

El flujo actual es:

```text
Cámara
   ↓
MediaPipe Pose
   ↓
Coordenadas de los puntos corporales
   ↓
Cálculos geométricos
   ↓
Umbrales manuales
   ↓
Oscilación corporal y alerta sonora
```

En `evaluacion.py` se compara la oscilación corporal registrada con los ojos
abiertos y cerrados. Un aumento durante la fase de ojos cerrados se informa
como un hallazgo de la prueba, sin interpretarlo como diagnóstico clínico.

## 2. Archivos principales

| Archivo | Función |
|---|---|
| `evaluacion.py` | Prueba de Romberg y cálculo de la oscilación corporal. |
| `ejercicio1.py` | Marcha tándem, también conocida como talón-punta. |
| `ejercicio2.py` | Apoyo unipodal intercalado. |
| `ejercicio3.py` | Postura del árbol adaptada. |
| `alertas_sonoras.py` | Emisión de alertas o mensajes de audio. |
| `requirements.txt` | Dependencias de Python del proyecto. |

## 3. Cómo iniciar el proyecto

Abrir PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\ADMIN\Desktop\MODELO-TESIS2026"
```

Ejecutar la prueba de Romberg:

```powershell
.\venv\Scripts\python.exe evaluacion.py
```

Ejecutar los ejercicios:

```powershell
.\venv\Scripts\python.exe ejercicio1.py
.\venv\Scripts\python.exe ejercicio2.py
.\venv\Scripts\python.exe ejercicio3.py
```

La cámara debe estar disponible y el usuario debe colocarse dentro del encuadre. Si el programa no puede abrir la cámara, debe comprobarse que ninguna otra aplicación la esté utilizando.

## 4. Reglas que existen actualmente

### 4.1 Prueba de Romberg

En `evaluacion.py` se registra la oscilación del centro corporal con los ojos
abiertos y cerrados:

```text
oscilacion = distancia(centro_actual, centro_inicial)
             / ancho_de_hombros × 100
```

La comparación utilizada es:

```text
oscilacion_ojos_cerrados > oscilacion_ojos_abiertos
    → mayor oscilación con ojos cerrados y alerta
```

La función devuelve un diccionario con el promedio, máximo y número de
muestras de cada fase:

```python
{
    "ojos_abiertos": {
        "oscilacion_maxima": valor,
        "oscilacion_promedio": valor,
        "muestras": cantidad
    },
    "ojos_cerrados": {
        "oscilacion_maxima": valor,
        "oscilacion_promedio": valor,
        "muestras": cantidad
    },
    "diferencia_oscilacion": valor,
    "estado": "Mayor oscilación con ojos cerrados"
        o "Sin aumento evidente de oscilación"
}
```

Los puntos solo se utilizan cuando su visibilidad estimada por MediaPipe es
igual o superior a `0.5`. Actualmente el resultado se devuelve en memoria,
pero no se guarda en un archivo ni en una base de datos.

### 4.2 Marcha tándem

En `ejercicio1.py` se mide el desplazamiento lateral del centro de las
caderas respecto a una referencia inicial. El desplazamiento se normaliza con
el ancho de los hombros para reducir el efecto de la resolución y distancia de
la cámara. La cámara debe ubicarse de frente:

```text
desvio_lateral =
    abs(centro_caderas_actual - centro_caderas_inicial)
    / ancho_hombros × 100
```

La regla actual considera:

```text
desequilibrio_lateral <= 5.0 → postura estable
desequilibrio_lateral > 5.0  → desequilibrio lateral
```

### 4.3 Apoyo unipodal

En `ejercicio2.py` se compara la altura de ambos tobillos. Debido a que en la imagen el eje `y` aumenta hacia abajo, un valor menor indica que el pie está más elevado. Antes de calcular la condición se verifica la visibilidad de caderas, rodillas y tobillos.

También se calcula y muestra el ángulo de la pierna de apoyo utilizando tres puntos:

```text
cadera → rodilla → tobillo
```

La función `calcular_angulo` obtiene el ángulo entre esos segmentos.

### 4.4 Postura del árbol

En `ejercicio3.py` se calcula el centro de los hombros y el centro de las caderas:

```text
centro_hombros_x = (hombro_izquierdo_x + hombro_derecho_x) / 2
centro_caderas_x = (cadera_izquierda_x + cadera_derecha_x) / 2
```

La desviación del tronco se calcula mediante:

```text
desviacion_tronco = abs(centro_hombros_x - centro_caderas_x) × 100
```

Además, el ejercicio comprueba la silueta de la postura:

- Un tobillo debe acercarse a la rodilla o pantorrilla de la pierna de apoyo.
- La rodilla de la pierna elevada debe abrirse hacia afuera.
- La pierna elevada debe estar flexionada.
- El tronco debe conservar su alineación.

La silla es opcional. Puede utilizarse como apoyo de seguridad, pero no se exige ni se intenta detectar como objeto. Las manos pueden mantenerse juntas frente al pecho, como en la primera imagen, o utilizarse para apoyo, como en la segunda imagen; por ello no son una condición obligatoria para aprobar la postura.

La regla actual es:

```text
pie elevado cerca de la pantorrilla y rodilla abierta → silueta de árbol
pie sin posición de pantorrilla o rodilla sin apertura → solicitar ajuste
desviacion_tronco >= 3.5 → tronco inclinado
```

## 4.5 Correcciones técnicas aplicadas

Se realizaron las siguientes correcciones sin reemplazar los ejercicios:

- Se comprueba que la cámara se haya abierto antes de iniciar.
- Se comprueba que cada fotograma se haya leído correctamente.
- Se validan niveles de visibilidad de los puntos corporales antes de calcular métricas.
- Se reemplazaron bloques `except Exception` que ocultaban errores de programación por condiciones explícitas de pose no detectada.
- Se garantiza el cierre de MediaPipe, la cámara y las ventanas de OpenCV mediante `finally`.
- Se eliminaron importaciones que no se utilizaban.
- La evaluación inicial ahora calcula realmente `inclinacion_tronco` y actualiza el estado de la sesión.
- La marcha tándem solicita una vista frontal, coherente con la métrica de anchura corporal.
- El apoyo unipodal muestra el ángulo de la pierna de soporte.
- La postura del árbol verifica la silueta de árbol: pie elevado hacia la pantorrilla, rodilla abierta y pierna flexionada; antes solo evaluaba la inclinación del tronco y no confirmaba la forma del ejercicio.
- La postura del árbol permite la variante con silla de la segunda imagen y no exige una posición fija de las manos.

Estas reglas son criterios técnicos iniciales y no deben interpretarse como umbrales clínicos validados hasta realizar una recolección de datos y una evaluación con participantes.

## 5. Qué significa entrenar estos modelos

No es necesario comenzar entrenando nuevamente MediaPipe Pose. MediaPipe ya resuelve la detección de los puntos corporales.

La opción recomendada es entrenar un segundo modelo que reciba las coordenadas y métricas obtenidas por MediaPipe y clasifique el estado de la postura:

```text
Cámara
   ↓
MediaPipe Pose, modelo preentrenado
   ↓
Características numéricas
   ↓
Clasificador entrenado con datos del proyecto
   ↓
Postura correcta o tipo de error
```

Este enfoque permite sustituir o complementar los umbrales fijos con un modelo aprendido a partir de ejemplos reales.

## 6. Modelo recomendado para comenzar

Para la primera versión se recomienda utilizar `RandomForestClassifier` de `scikit-learn`, porque:

- Puede funcionar bien con conjuntos de datos pequeños o medianos.
- No requiere una red neuronal compleja.
- Permite trabajar con características numéricas.
- Es relativamente fácil de interpretar.
- Puede servir como línea base para la tesis.

Después se pueden comparar otros métodos:

- Regresión logística.
- Máquina de vectores de soporte (`SVC`).
- XGBoost.
- Redes neuronales, si se cuenta con suficientes datos.

## 7. Definición de las clases

Antes de recolectar datos es necesario definir qué debe aprender el modelo. Una primera versión sencilla puede utilizar dos clases:

```text
correcta
incorrecta
```

Una versión más detallada puede utilizar:

```text
correcta
inclinacion_tronco
perdida_equilibrio
pierna_incorrecta
```

Las clases deben representar situaciones observables y deben tener suficientes ejemplos. No conviene mezclar diferentes errores en una misma clase si después se necesita identificar exactamente cuál es el problema.

## 8. Características que se pueden utilizar

Las características son los valores numéricos que se entregan al clasificador. Por ejemplo, para la postura del árbol:

- `desviacion_tronco`.
- `diferencia_altura_pies`.
- `angulo_rodilla_izquierda`.
- `angulo_rodilla_derecha`.
- Distancia entre los hombros.
- Distancia entre las caderas.
- Confianza de los puntos detectados por MediaPipe.

Es preferible utilizar métricas normalizadas o relativas cuando sea posible. Por ejemplo, las distancias corporales pueden dividirse por una longitud de referencia del cuerpo para reducir el efecto de la distancia entre la persona y la cámara.

## 9. Recolección de datos

El programa actual calcula métricas, pero todavía no las guarda como conjunto de datos. El siguiente paso es crear un recolector que guarde una fila por observación.

Una fila podría tener la siguiente estructura:

```csv
persona,ejercicio,desviacion_tronco,diferencia_altura_pies,angulo_rodilla_izquierda,angulo_rodilla_derecha,etiqueta
p01,arbol,2.1,0.18,86.4,88.2,correcta
p01,arbol,6.7,0.04,72.2,75.1,inclinacion_tronco
p02,arbol,1.9,0.21,89.1,90.4,correcta
```

El recolector debe:

1. Abrir la cámara.
2. Detectar los puntos con MediaPipe.
3. Calcular las características.
4. Asociar una etiqueta indicada por el investigador.
5. Guardar los valores en un archivo CSV.

Se deben recolectar ejemplos de todas las clases. Para cada persona pueden registrarse varios segundos de cada condición, pero las muestras consecutivas no deben considerarse como observaciones completamente independientes sin evaluar la dependencia temporal.

## 10. Recomendaciones para la muestra

Los datos deben incluir, en lo posible:

- Varias personas.
- Diferentes alturas y complexiones.
- Distintas distancias a la cámara.
- Variaciones razonables de iluminación.
- Diferentes ángulos de la cámara, si forman parte del caso de uso.
- Ejecuciones correctas e incorrectas.

Es importante que los datos de una misma persona no aparezcan simultáneamente en entrenamiento y prueba. Si ocurre, el resultado puede parecer muy bueno porque el modelo aprende características particulares de esa persona.

Una división inicial puede ser:

```text
70 % entrenamiento
15 % validación
15 % prueba
```

La división debe hacerse por persona cuando el objetivo sea evaluar el comportamiento con usuarios nuevos.

## 11. Dependencias para entrenar

El proyecto ya tiene varias dependencias relacionadas con visión artificial. Para entrenar un clasificador con CSV se pueden instalar:

```powershell
.\venv\Scripts\python.exe -m pip install pandas scikit-learn joblib
```

Estas dependencias deberían agregarse posteriormente a `requirements.txt` para que el entorno pueda reproducirse.

## 12. Ejemplo de entrenamiento

Una vez creado el archivo `datos/postura_arbol.csv`, se puede crear `entrenar_modelo.py` con una estructura como la siguiente:

```python
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


datos = pd.read_csv("datos/postura_arbol.csv")

caracteristicas = [
    "desviacion_tronco",
    "diferencia_altura_pies",
    "angulo_rodilla_izquierda",
    "angulo_rodilla_derecha",
]

X = datos[caracteristicas]
y = datos["etiqueta"]

X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

modelo = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
)

modelo.fit(X_entrenamiento, y_entrenamiento)

predicciones = modelo.predict(X_prueba)
print(classification_report(y_prueba, predicciones))

joblib.dump(
    {
        "modelo": modelo,
        "caracteristicas": caracteristicas,
    },
    "modelos/postura_arbol.joblib",
)
```

Este ejemplo es una base de trabajo. Para una evaluación metodológicamente más sólida, la división de datos debe hacerse por persona y debe existir un conjunto de prueba separado que no haya sido utilizado durante el entrenamiento.

## 13. Uso del modelo en tiempo real

Después de entrenar el modelo, el programa debe cargar el archivo generado y construir una entrada con el mismo orden y nombres de características utilizados durante el entrenamiento:

```python
import joblib
import pandas as pd


datos_modelo = joblib.load("modelos/postura_arbol.joblib")
modelo = datos_modelo["modelo"]
caracteristicas = datos_modelo["caracteristicas"]

entrada = pd.DataFrame([{
    "desviacion_tronco": desviacion_tronco,
    "diferencia_altura_pies": diferencia_altura_pies,
    "angulo_rodilla_izquierda": angulo_rodilla_izquierda,
    "angulo_rodilla_derecha": angulo_rodilla_derecha,
}])

estado = modelo.predict(entrada[caracteristicas])[0]
estado_texto = f"Estado: {estado}"
```

La entrada durante la predicción debe tener las mismas unidades, transformaciones y características usadas durante el entrenamiento. Si se cambia una fórmula o se agrega una característica, el modelo debe volver a entrenarse o debe actualizarse el pipeline de procesamiento.

## 14. Evaluación del modelo

No se debe evaluar solamente con exactitud (`accuracy`). También se recomienda reportar:

- Precisión.
- Sensibilidad o `recall`.
- Puntuación F1.
- Matriz de confusión.
- Resultados por clase.
- Tiempo de inferencia.

En este proyecto, la sensibilidad de la clase de error puede ser especialmente importante: un sistema que no detecta una pérdida de equilibrio puede ser más problemático que uno que ocasionalmente genere una alerta de más.

También se debe comparar:

1. El método actual basado en umbrales.
2. El clasificador entrenado.

La comparación debe utilizar las mismas personas, condiciones y conjunto de prueba.

## 15. Orden recomendado de trabajo

1. Ejecutar y comprobar los cuatro programas actuales.
2. Verificar que los puntos de MediaPipe se detecten correctamente.
3. Revisar y documentar las fórmulas de cada ejercicio.
4. Elegir un solo ejercicio para la primera prueba, preferiblemente la postura del árbol.
5. Definir las clases: `correcta` e `incorrecta`.
6. Crear el recolector de datos en CSV.
7. Recolectar datos de varias personas.
8. Separar los datos por persona en entrenamiento y prueba.
9. Entrenar un `RandomForestClassifier`.
10. Evaluar el modelo con métricas y matriz de confusión.
11. Compararlo contra los umbrales actuales.
12. Integrar el modelo en tiempo real.
13. Repetir el proceso para los demás ejercicios.
14. Realizar una evaluación final con personas que no participaron en el entrenamiento.

## 16. Consideraciones para la tesis

El sistema debe describirse como un enfoque de dos etapas:

1. **Estimación de pose:** MediaPipe Pose obtiene los puntos corporales desde la imagen.
2. **Clasificación de postura:** un modelo entrenado con datos del proyecto clasifica las características calculadas.

La detección de pose y la clasificación no son el mismo modelo. Esta separación facilita explicar el método, recolectar datos y comparar los umbrales manuales con el aprendizaje automático.

También es importante aclarar que el sistema constituye una herramienta de apoyo para la evaluación del movimiento y no sustituye una valoración clínica profesional. Las alertas y clasificaciones deben interpretarse dentro del alcance definido para la investigación.

## 17. Resumen

Sí, los modelos se pueden entrenar, pero el proyecto actual todavía utiliza MediaPipe Pose más reglas manuales. El inicio recomendado es:

```text
1. Elegir un ejercicio.
2. Guardar sus métricas en un CSV.
3. Etiquetar cada muestra.
4. Entrenar un Random Forest.
5. Evaluarlo con datos de personas no vistas.
6. Integrarlo en el programa de cámara.
```

El primer objetivo práctico debe ser crear un conjunto de datos confiable para un solo ejercicio. La calidad y diversidad de los datos será más importante que comenzar con un algoritmo complejo.
