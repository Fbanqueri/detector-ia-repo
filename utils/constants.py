import os

# Carpeta temporal del sistema donde se clonarán los repositorios
TMP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "detector_ia_repos")

#Carpetas que se ignoran para no saturar el analisis
IGNORE_DIRS = {
    # Web / JS
    'node_modules', '.next', 'dist', 'out', 'build', 
    # Python
    'venv', '.venv', 'env', '__pycache__', '.pytest_cache', 
    # Otros / IDEs
    '.git', '.github', '.vscode', '.idea', 'vendor'
}

# Extensiones Permitidas para Escaneo de código fuente
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', 
    '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.rs'
}

#modelo local en Ollama
MODEL_ID = "qwen2.5-coder:1.5b"

# Umbrales visuales de sospecha
THRESHOLD_LOW = 40.0
THRESHOLD_MEDIUM = 70.0


