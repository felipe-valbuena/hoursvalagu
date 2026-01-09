from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re
import os

app = Flask(__name__)

def obtener_horas(modelo, fecha_inicio, fecha_fin, sitio):
    url = f"https://www.{sitio}.com/user/{modelo}.html"

    # Optimizaciones de velocidad para Render
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    # Bloquear imágenes para que cargue mas rápido
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None 
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Timeout agresivo para que no se cuelgue cargando
        driver.set_page_load_timeout(20) 
        driver.get(url)
        
        # Espera reducida a 10s como sugirió el experto
        wait = WebDriverWait(driver, 10) 

        CONTAINER_SELECTOR = "div.activity_logs_container"
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CONTAINER_SELECTOR)))
            activity_container = driver.find_element(By.CSS_SELECTOR, CONTAINER_SELECTOR)
            driver.execute_script("arguments[0].classList.add('visible');", activity_container)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.activity_logs_content p")))
        except Exception:
            driver.quit()
            return None, "No se encontraron registros o la página tardó mucho."
            
        registros_html = driver.find_elements(By.CSS_SELECTOR, "div.activity_logs_content p")
        
        registros = []
        total_horas = 0
        total_minutos = 0
        fecha_ini = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

        for r in registros_html:
            texto = r.text.strip()
            match = re.search(r"(\d{4}-\d{2}-\d{2}).*?(\d{1,2}) Hours (\d{1,2}) Minutes", texto)
            if match:
                f_str, h_str, m_str = match.groups()
                try:
                    f_reg = datetime.strptime(f_str, "%Y-%m-%d")
                    if fecha_ini <= f_reg <= fecha_fin:
                        h, m = int(h_str), int(m_str)
                        total_horas += h
                        total_minutos += m
                        registros.append((f_str, f"{h} horas {m} minutos"))
                except ValueError: continue
        
        total_horas += total_minutos // 60
        total_minutos %= 60
        driver.quit()

        return {
            "modelo": modelo, "sitio": sitio, "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin, "total_horas": total_horas,
            "total_minutos": total_minutos, "registros": registros
        }, None

    except Exception as e:
        if driver: driver.quit()
        return None, f"Error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    resultado, error = None, None
    if request.method == "POST":
        modelo = request.form.get("modelo")
        f_ini = request.form.get("fecha_inicio")
        f_fin = request.form.get("fecha_fin")
        sitio = request.form.get("sitio", "striphours")
        
        if not (modelo and f_ini and f_fin):
             error = "Faltan datos."
        else:
            try:
                if datetime.strptime(f_ini, "%Y-%m-%d") > datetime.strptime(f_fin, "%Y-%m-%d"):
                    error = "Fechas incorrectas."
                else:
                    resultado, error = obtener_horas(modelo, f_ini, f_fin, sitio)
            except ValueError: error = "Error en fechas."
    return render_template("index.html", resultado=resultado, error=error)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
