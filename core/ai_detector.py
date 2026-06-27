import requests
import re
import json
from typing import Dict, Any
from utils.constants import MODEL_ID

def analyze_code_snippet(code_text: str) -> float:
    """
    Analiza un archivo de código y determina la probabilidad (de 0 a 100) 
    de que haya sido generado por una IA, consultando al modelo local 
    qwen2.5-coder:1.5b a través de Ollama.
    """
    if not code_text or not code_text.strip():
        return 0.0

    # Filtro de longitud de archivo (líneas reales sin contar vacías)
    real_lines = [line for line in code_text.splitlines() if line.strip()]
    if len(real_lines) < 25:
        print(f"[AI Detector] Archivo corto ({len(real_lines)} líneas de código real). Asignando score automático de 15.0%.")
        return 15.0

    system_prompt = (
        "Actúas como un auditor forense de código. Tu objetivo es diferenciar código escrito por un humano experto de código generado por asistentes de IA (Copilot, ChatGPT). El código humano estructurado antiguo tiende a ser limpio pero puede incluir ligeras inconsistencias de formato, modismos de autor o ausencia de comentarios redundantes. La IA actual peca de ser excesivamente predecible, con comentarios perfectos y redundantes en inglés que explican cada línea, y estructuras de diseño idénticas sin desviaciones. Analizá el archivo y respondé ÚNICAMENTE con el JSON: {\"ai_probability\": X} donde X es entre 0 y 100. Sé conservador: si el código es estándar pero no muestra vicios claros de Copilot, el score debe ser menor a 30."
    )

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": MODEL_ID,
        "prompt": code_text,
        "system": system_prompt,
        "stream": False
    }

    score = 0.0

    try:
        response = requests.post(url, json=payload, timeout=45)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "").strip()
            
            print(f"--- [DEBUG] Respuesta cruda de Qwen: '{response_text}' ---")
            
            parsed_json = False
            # 1. Intentar parsear el JSON completo directamente
            try:
                data = json.loads(response_text)
                if "ai_probability" in data:
                    score = float(data["ai_probability"])
                    parsed_json = True
            except Exception:
                pass
            
            # 2. Intentar buscar un bloque JSON { ... } si el LLM incluyó texto explicativo o markdown
            if not parsed_json:
                try:
                    json_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(0))
                        if "ai_probability" in data:
                            score = float(data["ai_probability"])
                            parsed_json = True
                except Exception:
                    pass

            # 3. Intentar extraer con regex específica
            if not parsed_json:
                match = re.search(r'"ai_probability"\s*:\s*(100|[0-9]{1,2})', response_text)
                if match:
                    score = float(match.group(1))
                    parsed_json = True

            # 4. Fallback final buscando cualquier entero entre 0 y 100
            if not parsed_json:
                match_fallback = re.search(r'\b(100|[0-9]{1,2})\b', response_text)
                if match_fallback:
                    score = float(match_fallback.group(1))
                else:
                    print(f"[AI Detector] Respuesta no parseable de Ollama: '{response_text}'")
                    score = 0.0
            
            print(f"--- [DEBUG] Score extraído final por la Regex: {score} ---")
        else:
            print(f"[AI Detector] Error de Ollama (Status {response.status_code}): {response.text}")
            score = 0.0
    except Exception as e:
        print(f"[AI Detector] Error de conexión o petición con Ollama: {str(e)}")
        score = 0.0

    # 1. Amplificación de confidencia 
    score_base = score
    if score_base >= 45.0:
        score_amplified = 50.0 + (score_base - 50.0) * 1.6
        score_final = min(100.0, max(0.0, score_amplified))
        print(f"[Forense] Archivo analizado. Base: {score_base}% -> Amplificado: {score_final}%")
    else:
        score_final = score_base
        print(f"[Forense] Archivo analizado (sin amplificación). Base: {score_base}% -> Score final: {score_final}%")

    return score_final
