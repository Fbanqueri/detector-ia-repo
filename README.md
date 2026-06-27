# Detector de IA en Repositorios (Local)

Este proyecto es una herramienta de auditoría automatizada diseñada para analizar el código fuente de repositorios públicos de GitHub y determinar la probabilidad de que haya sido generado por asistentes de Inteligencia Artificial (como ChatGPT, GitHub Copilot, etc.). Todo el análisis se ejecuta de manera **100% local** garantizando la privacidad del código.

## Flujo de Trabajo

El flujo de ejecución de la herramienta consta de los siguientes pasos:

1. **Entrada de URL:** El usuario ingresa la URL pública del repositorio de GitHub en la interfaz interactiva.
2. **Clonado Seguro:** La aplicación clona el repositorio (o una rama/subdirectorio específico) en un directorio local temporal usando Git.
3. **Escaneo y Filtrado:** Se realiza un recorrido recursivo por el repositorio clonado. Se filtran carpetas comunes de dependencias, entornos virtuales y compilación (por ejemplo, `node_modules`, `venv`, `.git`) y se seleccionan únicamente archivos de código válidos (con extensiones como `.py`, `.js`, `.ts`, `.cpp`, etc.). Adicionalmente, se buscan patrones y comentarios típicos generados por IA a través de expresiones regulares.
4. **Análisis por IA (Local):** El contenido de cada archivo de código calificado es enviado a un servidor local de Ollama para ser evaluado por el modelo de lenguaje **qwen2.5-coder:1.5b**.
5. **Cálculo y Presentación del Reporte:** Se procesa una métrica de sospecha general (promedio ponderado basado en las líneas de código de cada archivo) y se muestran los resultados en la interfaz de Streamlit mediante indicadores visuales premium y un desglose detallado por archivo.
6. **Limpieza de Temporales:** El directorio temporal donde se clonó el repositorio se elimina automáticamente al finalizar el análisis, tanto en ejecuciones exitosas como si se produce algún error.

## Librerías Utilizadas

Este proyecto utiliza las siguientes dependencias de software:

* **Streamlit**
* **GitPython**
* **Requests**
* **python-magic**
* **python-magic-bin**
