import os
import streamlit as m_streamlit
from core.cloner import clone_repository, clean_temporary_dir
from core.file_scanner import scan_repository_files
from core.ai_detector import analyze_code_snippet
from utils.constants import THRESHOLD_LOW, THRESHOLD_MEDIUM


m_streamlit.set_page_config(
    page_title="Detector de IA en Repositorios",
    page_icon="🤖",
    layout="wide"
)

def calculate_final_score(file_results: list) -> float:
    """
    Calcula el porcentaje final de sospecha de IA en el repositorio como un
    promedio ponderado basado en la cantidad de líneas de código de cada archivo.
    """
    total_lines = sum(file.get("total_lines", 0) for file in file_results)
    if total_lines == 0:
        return 0.0
    
    weighted_sum = sum(file.get("ai_score", 0.0) * file.get("total_lines", 0) for file in file_results)
    return round(weighted_sum / total_lines, 2)


m_streamlit.title("🤖 Analizador de Repositorios - Detector de IA (Local)")
m_streamlit.markdown(
    "Ingresá la URL pública de un repositorio de GitHub para auditar la procedencia de su código. "
    "El análisis se ejecuta de forma **100% local** evaluando la estructura de cada archivo de código fuente "
    "con el modelo local **qwen2.5-coder:1.5b** corriendo en Ollama."
)


repo_url = m_streamlit.text_input("URL del Repositorio de GitHub:", placeholder="https://github.com/usuario/nombre-repo")

if m_streamlit.button("Iniciar Escaneo Automatizado", type="primary"):
    if not repo_url or "github.com" not in repo_url:
        m_streamlit.error("Por favor, ingresá una URL válida de GitHub (ej: https://github.com/autor/repo).")
    else:
        repo_root = None
        repo_path = None
        try:
            
            status_box = m_streamlit.empty()
            progress_bar = m_streamlit.progress(0)

            # Paso 1: Clonado Seguro
            status_box.info("📥 Paso 1/3: Clonando repositorio en carpeta temporal local...")
            progress_bar.progress(15)
            repo_root, repo_path = clone_repository(repo_url)

            # Paso 2: Escaneo de Archivos
            status_box.info("🔍 Paso 2/3: Filtrando dependencias y escaneando archivos de código...")
            progress_bar.progress(40)
            file_results = scan_repository_files(repo_path)

            if not file_results:
                raise ValueError("No se encontraron archivos de código fuente válidos para analizar en este repositorio.")

            # Paso 3: Análisis con Ollama
            total_files = len(file_results)
            status_box.info(f"🧠 Paso 3/3: Iniciando análisis con Ollama...")
            
            for idx, file in enumerate(file_results, 1):
                rel_path = os.path.relpath(file["file_path"], repo_path) if repo_path else file["file_path"]
                status_box.info(f"🧠 Paso 3/3: Analizando archivo {idx}/{total_files}: `{rel_path}`...")
                
                
                current_prog = int(40 + (idx / total_files) * 55)
                progress_bar.progress(current_prog)
                
                try:
                    with open(file["file_path"], 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    file["ai_score"] = analyze_code_snippet(content)
                except Exception as e:
                    print(f"[App] Error analizando {file['file_path']}: {e}")
                    file["ai_score"] = 0.0

            progress_bar.progress(100)
            status_box.empty() # Limpiamos los textos temporales de carga

            # --- PRESENTACIÓN DEL REPORTE FINAL ---
            m_streamlit.success("🎉 ¡Análisis completo!")
            
            final_score = calculate_final_score(file_results)
            hue = max(0, min(120, int(120 - (final_score * 1.2))))
            
            # Renderizar la barra de progreso horizontal con CSS premium
            progress_bar_html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 25px 0; padding: 20px; border-radius: 12px; background-color: #f8f9fa; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
                <div style="display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 10px; font-size: 1.15rem; color: #212529;">
                    <span>Sospecha General de IA (Promedio Ponderado)</span>
                    <span style="color: hsl({hue}, 85%, 40%); font-size: 1.3rem; font-weight: 700;">{final_score}%</span>
                </div>
                <div style="background-color: #e9ecef; border-radius: 20px; width: 100%; height: 28px; padding: 3px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06); overflow: hidden; display: flex; align-items: center;">
                    <div style="width: {final_score}%; height: 100%; background: linear-gradient(90deg, #28a745, hsl({hue}, 85%, 45%)); border-radius: 20px; transition: width 1s ease-in-out; min-width: 4%;"></div>
                </div>
            </div>
            """
            m_streamlit.markdown(progress_bar_html, unsafe_allow_html=True)

            # Mostrar el veredicto final según los umbrales
            if final_score > THRESHOLD_MEDIUM:
                m_streamlit.error(f"🚨 Alerta: Uso ALTO de IA en el repositorio ({final_score}%).")
            elif final_score >= THRESHOLD_LOW:
                m_streamlit.warning(f"⚠️ Advertencia: Uso MEDIO de IA en el repositorio ({final_score}%).")
            else:
                m_streamlit.success(f"✅ Uso BAJO de IA en el repositorio ({final_score}%).")

            m_streamlit.markdown("---")
            m_streamlit.markdown(f"### 📊 Detalle por Archivo")
            m_streamlit.write(f"Archivos de código fuente analizados: `{total_files}`")
            
            # Construir y renderizar tabla HTML detallada con badges de estado
            table_rows_html = ""
            for file in file_results:
                rel_path = os.path.relpath(file["file_path"], repo_path) if repo_path else file["file_path"]
                ai_score = file.get("ai_score", 0.0)
                lines = file.get("total_lines", 0)
                
                # Determinar badge
                if ai_score > THRESHOLD_MEDIUM:
                    badge_html = '<span style="background-color: #f8d7da; color: #721c24; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; border: 1px solid #f5c6cb;">Alto</span>'
                elif ai_score >= THRESHOLD_LOW:
                    badge_html = '<span style="background-color: #fff3cd; color: #856404; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; border: 1px solid #ffeeba;">Medio</span>'
                else:
                    badge_html = '<span style="background-color: #d4edda; color: #155724; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; border: 1px solid #c3e6cb;">Bajo</span>'
                
                table_rows_html += f"""
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 12px 15px; font-family: monospace; color: #333; text-align: left;">{rel_path}</td>
                    <td style="padding: 12px 15px; color: #495057; text-align: right;">{lines}</td>
                    <td style="padding: 12px 15px; font-weight: 600; color: #212529; text-align: right;">{ai_score}%</td>
                    <td style="padding: 12px 15px; text-align: center;">{badge_html}</td>
                </tr>
                """
            
            table_html = f"""
            <div style="overflow-x: auto; margin-top: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
                <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                    <thead>
                        <tr style="background-color: #f1f3f5; border-bottom: 2px solid #dee2e6;">
                            <th style="padding: 12px 15px; text-align: left; color: #495057; font-weight: 600;">Ruta del Archivo</th>
                            <th style="padding: 12px 15px; text-align: right; color: #495057; font-weight: 600; width: 120px;">Líneas</th>
                            <th style="padding: 12px 15px; text-align: right; color: #495057; font-weight: 600; width: 150px;">Sospecha de IA</th>
                            <th style="padding: 12px 15px; text-align: center; color: #495057; font-weight: 600; width: 120px;">Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
            """
            m_streamlit.markdown(table_html, unsafe_allow_html=True)

        except Exception as e:
            m_streamlit.error(f"Se produjo un error durante el procesamiento: {str(e)}")
            
        finally:
            # Importante: Garantizamos que la carpeta temporal se borre pase lo que pase
            if repo_root:
                clean_temporary_dir(repo_root)