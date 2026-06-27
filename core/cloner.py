import os
import shutil
import uuid
import git
from utils.constants import TMP_DIR

import re

def parse_github_url(url: str):
    """
    Parsea una URL de GitHub para extraer el repositorio base, la rama y el subdirectorio (si existen).
    """
    pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+)(?:/(.*))?)?"
    match = re.match(pattern, url.strip())
    if not match:
        # Fallback genérico si no es de GitHub
        return url, None, None
        
    owner = match.group(1)
    repo = match.group(2)
    # Limpiamos si termina en .git
    if repo.endswith(".git"):
        repo = repo[:-4]
        
    base_url = f"https://github.com/{owner}/{repo}"
    branch = match.group(3)
    subdir = match.group(4)
    
    return base_url, branch, subdir

def generate_unique_path() -> str:
    """Genera una ruta única dentro de la carpeta temporal para evitar colisiones."""
    unique_id = f"analysis_{uuid.uuid4().hex[:8]}"
    return os.path.join(TMP_DIR, unique_id)

def clone_repository(repo_url: str) -> tuple:
    """
    Clona un repositorio de GitHub (y maneja subdirectorios si están en la URL).
    Retorna una tupla: (ruta_clon_raiz, ruta_subdirectorio_a_escanear)
    """
    # la carpeta raíz temporal exista
    os.makedirs(TMP_DIR, exist_ok=True)
    
    # Generamos el destino para este clon específico
    target_path = generate_unique_path()
    
    base_url, branch, subdir = parse_github_url(repo_url)
    
    try:
        print(f"[Cloner] Clonando {base_url} en {target_path}...")
        
        # Copiamos variables de entorno y desactivamos los prompts interactivos
        my_env = os.environ.copy()
        my_env["GIT_TERMINAL_PROMPT"] = "0"
        my_env["GCM_INTERACTIVE"] = "never"
        my_env["GIT_ASKPASS"] = "echo"
        
        # Desactivamos el credential helper para no levantar popups de Windows
        clone_kwargs = {
            "env": my_env,
            "c": "credential.helper="
        }
        if branch:
            clone_kwargs["branch"] = branch
            
        # Equivale a 'git clone <url>'
        git.Repo.clone_from(base_url, target_path, allow_unsafe_options=True, **clone_kwargs)
        
        scan_path = target_path
        if subdir:
            # Reemplazar posibles barras diagonales del subdirectorio y normalizar la ruta
            scan_path = os.path.join(target_path, os.path.normpath(subdir))
            if not os.path.exists(scan_path):
                print(f"[Cloner] Alerta: El subdirectorio '{subdir}' no se encontró en el clon. Se escaneará la raíz.")
                scan_path = target_path
                
        return target_path, scan_path
        
    except Exception as e:
        # Si falla el clonado, nos aseguramos de no dejar carpetas a medias
        clean_temporary_dir(target_path)
        raise RuntimeError(f"Error al clonar el repositorio: {str(e)}")

def clean_temporary_dir(dir_path: str):
    """Fuerza la eliminación de la carpeta temporal al finalizar el análisis."""
    if dir_path and os.path.exists(dir_path):
        try:
            print(f"[Cloner] Limpiando carpeta temporal: {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)
        except Exception as e:
            print(f"[Cloner] Alerta al borrar la carpeta {dir_path}: {str(e)}")