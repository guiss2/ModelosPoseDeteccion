# Modelo de evaluación del equilibrio y la postura

Proyecto de tesis para analizar ejercicios de equilibrio mediante una cámara web, **MediaPipe Pose** y OpenCV. El sistema detecta puntos corporales, calcula métricas geométricas y genera alertas visuales y sonoras.

> **Importante:** el proyecto es una herramienta de apoyo para la investigación. Los umbrales actuales son valores técnicos iniciales y no sustituyen una evaluación clínica profesional.

## Características

- Detección de puntos corporales en tiempo real mediante MediaPipe Pose.
- Evaluación postural inicial.
- Marcha tándem o talón-punta.
- Apoyo unipodal intercalado.
- Postura del árbol adaptada.
- Alertas sonoras mediante pitidos y síntesis de voz.
- Validación de visibilidad de los puntos corporales.
- Liberación segura de la cámara y de las ventanas de OpenCV.

## Requisitos

- Windows.
- Python compatible con el entorno virtual del proyecto.
- Cámara web.
- Dependencias indicadas en `requirements.txt`.

El entorno virtual `venv` es local y está excluido mediante `.gitignore`. No debe subirse al repositorio.

## Instalación

Abrir PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\ADMIN\Desktop\MODELO-TESIS2026"
```

Si todavía no existe el entorno virtual, crearlo con:

```powershell
python -m venv venv
```

Activarlo:

```powershell
.\venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, se puede utilizar directamente el ejecutable del entorno virtual:

```powershell
.\venv\Scripts\python.exe evaluacion.py
```

## Ejecución

### Evaluación postural inicial

```powershell
.\venv\Scripts\python.exe evaluacion.py
```

Esta evaluación calcula:

- Desnivel entre los hombros.
- Inclinación horizontal del tronco.
- Estado general de la postura.

Presionar `ESC` para finalizar y conservar el último resultado válido en memoria.

### Ejercicio 1: marcha tándem

```powershell
.\venv\Scripts\python.exe ejercicio1.py
```

La persona debe colocarse de frente a la cámara. El programa compara el ancho de los hombros con el ancho de las caderas para estimar el desequilibrio lateral.

Presionar `q` para salir.

### Ejercicio 2: apoyo unipodal

```powershell
.\venv\Scripts\python.exe ejercicio2.py
```

El programa identifica qué pie está elevado, determina la pierna de soporte y calcula el ángulo formado por cadera, rodilla y tobillo.

Presionar `q` para salir.

### Ejercicio 3: postura del árbol adaptada

```powershell
.\venv\Scripts\python.exe ejercicio3.py
```

El programa comprueba:

1. Que exista una diferencia de altura entre los pies, como indicador de apoyo unipodal.
2. Que el tronco conserve una alineación adecuada.

Presionar `q` para salir.

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `evaluacion.py` | Evaluación postural inicial. |
| `ejercicio1.py` | Marcha tándem. |
| `ejercicio2.py` | Apoyo unipodal y cálculo de ángulos. |
| `ejercicio3.py` | Postura del árbol adaptada. |
| `alertas_sonoras.py` | Pitidos y mensajes de voz. |
| `requirements.txt` | Dependencias del proyecto. |
| `DOCUMENTACION_ENTRENAMIENTO.md` | Documentación detallada del análisis, las métricas y el entrenamiento. |
| `.gitignore` | Archivos locales excluidos de Git. |

## Flujo de funcionamiento

```text
Cámara
   ↓
MediaPipe Pose
   ↓
Puntos corporales
   ↓
Métricas geométricas
   ↓
Umbrales técnicos
   ↓
Estado de equilibrio y alerta
```

MediaPipe Pose es un modelo preentrenado. Actualmente el proyecto no entrena nuevamente ese modelo. La etapa de aprendizaje automático prevista consiste en entrenar un clasificador propio utilizando las métricas obtenidas por MediaPipe.

## Umbrales actuales

Los valores actuales son criterios iniciales que deben validarse con datos reales:

| Métrica | Umbral inicial |
|---|---:|
| Desnivel de hombros | `3.0` |
| Desequilibrio lateral en marcha tándem | `5.0` |
| Diferencia de altura de pies para apoyo unipodal | `0.05` |
| Desviación del tronco en postura del árbol | `3.5` |
| Visibilidad mínima de puntos corporales | `0.5` |

Estos valores no deben considerarse resultados clínicamente validados hasta realizar una evaluación con participantes y comparar las predicciones con una referencia adecuada.

## Entrenamiento futuro

El plan recomendado es:

1. Elegir un ejercicio, preferiblemente la postura del árbol.
2. Definir las clases, por ejemplo `correcta` e `incorrecta`.
3. Crear un recolector de datos.
4. Guardar las métricas en archivos CSV.
5. Recolectar datos de varias personas.
6. Separar entrenamiento y prueba por persona.
7. Entrenar un `RandomForestClassifier`.
8. Evaluar precisión, sensibilidad, F1 y matriz de confusión.
9. Comparar el clasificador con los umbrales actuales.
10. Integrar el modelo validado en la ejecución en tiempo real.

La guía completa se encuentra en [DOCUMENTACION_ENTRENAMIENTO.md](DOCUMENTACION_ENTRENAMIENTO.md).

## Recomendaciones para las pruebas

- Mantener todo el cuerpo dentro del encuadre.
- Utilizar buena iluminación.
- Evitar que otra aplicación utilice la cámara.
- Realizar las pruebas con un soporte cercano cuando se evalúe el equilibrio.
- No interpretar una alerta del programa como diagnóstico médico.
- Registrar las condiciones de la cámara y de la persona durante la recolección de datos.

## Verificación básica

Para comprobar que los archivos Python tienen sintaxis válida:

```powershell
.\venv\Scripts\python.exe -m compileall -q evaluacion.py ejercicio1.py ejercicio2.py ejercicio3.py alertas_sonoras.py
```

Si el comando termina sin mostrar errores, la compilación sintáctica básica fue correcta. La ejecución completa requiere una cámara disponible y un entorno gráfico compatible con OpenCV.

## Licencia y uso

Este archivo no define todavía una licencia de distribución. Antes de publicar el proyecto, se debe seleccionar una licencia y revisar las condiciones de uso de las dependencias externas.
