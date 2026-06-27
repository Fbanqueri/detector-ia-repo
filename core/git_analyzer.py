import git
import os
from datetime import datetime
from typing import Dict, Any, List
from utils.constants import LINES_PER_MINUTE_THRESHOLD, ALLOWED_EXTENSIONS, IGNORE_DIRS

def analyze_commit_history(repo_path: str) -> Dict[str, Any]:
    """
    Analiza el historial de commits del repositorio clonado localmente.
    Calcula la velocidad de adición de código entre commits consecutivos y detecta 
    heurísticas sospechosas (pocos commits con mucho código, o commits ultrarrápidos).
    """
    try:
        # Abrimos el repositorio local con GitPython
        repo = git.Repo(repo_path)
        
        # Obtenemos la lista de commits en orden cronológico inverso (del más nuevo al más viejo)
        commits = list(repo.iter_commits())
        total_commits = len(commits)
        git_alerts = []
        highest_speed = 0.0
        suspicious_commit_count = 0
        
        # 1. Calcular el total de líneas de código fuente actual en el repositorio
        total_lines_of_code = 0
        for root, dirs, files in os.walk(repo_path):
           
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in ALLOWED_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines_of_code += sum(1 for _ in f)
                    except Exception:
                        continue
        
        # 2. Heurística de Repositorio con menos de 3 commits totales pero mucho código
        if total_commits < 3:
            if total_lines_of_code > 250:
                git_score = 95.0
                git_alerts.append({
                    "commit_sha": "N/A",
                    "author": "N/A",
                    "date": "N/A",
                    "lines_added": total_lines_of_code,
                    "time_diff_seconds": 0,
                    "lines_per_minute": 0.0,
                    "message": f"Sospechoso: Repositorio con solo {total_commits} commits pero con {total_lines_of_code} líneas de código (posible copy-paste directo)."
                })
            else:
                git_score = 0.0
                
            return {
                "total_commits": total_commits,
                "git_alerts": git_alerts,
                "highest_speed": 0.0,
                "suspicious_commit_count": len(git_alerts),
                "git_score": git_score
            }
            
        # 3. Analizar los commits consecutivos para calcular velocidad de adición
        for i in range(len(commits) - 1):
            current_commit = commits[i]
            previous_commit = commits[i + 1] 
            
            # Calcular la diferencia de tiempo
            time_current = datetime.fromtimestamp(current_commit.committed_date)
            time_previous = datetime.fromtimestamp(previous_commit.committed_date)
            time_diff_seconds = (time_current - time_previous).total_seconds()
            time_diff_minutes = time_diff_seconds / 60.0
            
            # Calcular cuántas líneas se agregaron en este commit comparado con el anterior
            diff_stats = repo.git.diff(previous_commit.hexsha, current_commit.hexsha, numstat=True)
            lines_added = 0
            for line in diff_stats.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        if parts[0] != '-':
                            lines_added += int(parts[0])
                    except ValueError:
                        continue
                        
            # Evaluar la velocidad de commits consecutivos si hay líneas agregadas
            if time_diff_minutes > 0 and lines_added > 0:
                lines_per_minute = lines_added / time_diff_minutes
                
                if lines_per_minute > highest_speed:
                    highest_speed = lines_per_minute
                
                # Si supera el umbral y el commit se hizo en menos de 5 minutos
                if lines_per_minute > LINES_PER_MINUTE_THRESHOLD and time_diff_seconds < 300:
                    suspicious_commit_count += 1
                    git_alerts.append({
                        "commit_sha": current_commit.hexsha[:7],
                        "author": current_commit.author.name,
                        "date": time_current.strftime("%Y-%m-%d %H:%M:%S"),
                        "lines_added": lines_added,
                        "time_diff_seconds": int(time_diff_seconds),
                        "lines_per_minute": round(lines_per_minute, 2),
                        "message": current_commit.message.strip()
                    })
                    
        # 4. Calcular el Score de Sospecha Git (0% a 100%)
        if total_commits > 1:
            suspicious_ratio = suspicious_commit_count / (total_commits - 1)
            # Si el 20% o más de los commits son sospechosos
            git_score = min(100.0, suspicious_ratio * 500.0)
            
            # Penalizamos si la velocidad punta es absurdamente alta
            if highest_speed > 500:
                git_score = max(git_score, 85.0)
            elif highest_speed > LINES_PER_MINUTE_THRESHOLD:
                git_score = max(git_score, 50.0)
        else:
            git_score = 0.0
            
        return {
            "total_commits": total_commits,
            "git_alerts": git_alerts,
            "highest_speed": round(highest_speed, 2),
            "suspicious_commit_count": suspicious_commit_count,
            "git_score": round(git_score, 2)
        }
        
    except Exception as e:
        print(f"[Git Analyzer] Alerta analizando el historial: {str(e)}")
        return {
            "total_commits": 0,
            "git_alerts": [],
            "highest_speed": 0.0,
            "suspicious_commit_count": 0,
            "git_score": 0.0
        }