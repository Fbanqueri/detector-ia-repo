import os
import re
from typing import List, Dict, Any
from utils.constants import IGNORE_DIRS, ALLOWED_EXTENSIONS

AI_COMMENT_PATTERNS = [
    re.compile(r"this function implements", re.IGNORECASE),
    re.compile(r"explicación del código", re.IGNORECASE),
    re.compile(r"note that this loop guarantees", re.IGNORECASE),
    re.compile(r"este método se encarga de", re.IGNORECASE),
    re.compile(r"```[a-zA-Z]*\s*$", re.IGNORECASE), 
    re.compile(r"here is the updated code", re.IGNORECASE)
]

def should_scan_file(file_path: str) -> bool:
    """Verifica si el archivo tiene una extensión permitida para el escaneo."""
    _, ext = os.path.splitext(file_path)
    return ext.lower() in ALLOWED_EXTENSIONS

def scan_file_for_regex(file_path: str) -> Dict[str, Any]:
    """
    Lee un archivo línea por línea buscando patrones de comentarios de IA.
    Retorna un diccionario con las alertas encontradas.
    """
    alerts = []
    total_lines = 0
    ai_comment_count = 0
    
    try:
      
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_idx, line in enumerate(f, 1):
                total_lines += 1
                clean_line = line.strip()
                
                # Evaluamos si la línea coincide con alguna expresión regular de nuestra lista
                for pattern in AI_COMMENT_PATTERNS:
                    if pattern.search(clean_line):
                        ai_comment_count += 1
                        alerts.append({
                            "line": line_idx,
                            "content": clean_line[:80], # Guardamos un fragmento para mostrarlo
                            "pattern_matched": pattern.pattern
                        })
                        break # Si ya matcheó un patrón, pasamos a la siguiente línea
                        
    except Exception as e:
        print(f"[Scanner] No se pudo leer el archivo {file_path}: {str(e)}")
        
    return {
        "file_path": file_path,
        "total_lines": total_lines,
        "ai_comment_count": ai_comment_count,
        "alerts": alerts
    }

def scan_repository_files(repo_path: str) -> List[Dict[str, Any]]:
    """
    Recorre el repositorio usando os.walk, aplicando la lista negra de carpetas
    y analizando los archivos de código válidos.
    """
    results = []
    print(f"[Scanner] Iniciando escaneo de archivos en: {repo_path}...")
    
    for root, dirs, files in os.walk(repo_path):
       
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            full_path = os.path.join(root, file)
            
            # Si el archivo pasa el filtro de extensiones, lo inspeccionamos
            if should_scan_file(full_path):
                file_analysis = scan_file_for_regex(full_path)
                # archivos que tengan código o texto analizable
                if file_analysis["total_lines"] > 0:
                    results.append(file_analysis)
                    
    return results