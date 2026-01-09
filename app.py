from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime
import re
import os

app = Flask(__name__)

def obtener_horas(modelo, fecha_inicio, fecha_fin, sitio):
    # Configuración de URL
    url = f"https://www.{sitio}.com/user/{modelo}.html"

    print("\n" + "!"*60)
    print(f"TRABAJANDO EN: {sitio.upper()}")
    print(f"URL REAL: {url}")
    print("!"*60 + "\n")

    # Configuración de Selenium para Render (Linux Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080") 

    driver = None 
    try:
        # En Render, Selenium buscará el binario instalado automáticamente
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        wait = WebDriverWait(driver, 30) 

        # --- Lógica original intacta ---
        CONTAINER_SELECTOR = "div.activity_logs_container"
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CONTAINER_SELECTOR)))
        except TimeoutException:
             driver.quit()
             return None, f"Error de carga: No se encontró el contenedor en {sitio}.com."

        try:
            activity_container = driver.find_element(By.CSS_SELECTOR, CONTAINER_SELECTOR)
            driver.execute_script("arguments[0].classList.add('visible');", activity_container)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.activity_logs_content p")))
        except TimeoutException:
            driver.quit()
            return None, "Fallo de renderizado: Los registros no aparecieron."
            
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
                fecha_str = match.group(1)
                horas_str = match.group(2)
                minutos_str = match.group(3)
                
                try:
                    fecha_registro = datetime.strptime(fecha_str, "%Y-%m-%d")
                    if fecha_ini <= fecha_registro <= fecha_fin:
                        horas = int(horas_str)
                        minutos = int(minutos_str)
                        total_horas += horas
                        total_minutos += minutos
                        registros.append((fecha_str, f"{horas} horas {minutos} minutos"))
                except ValueError:
                    continue
        
        total_horas += total_minutos // 60
        total_minutos = total_minutos % 60
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
    resultado = None
    error = None
    context = {"resultado": resultado, "error": error, "request": request} 

    if request.method == "POST":
        modelo = request.form.get("modelo")
        fecha_inicio = request.form.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin")
        sitio = request.form.get("sitio", "striphours")
        
        if not (modelo and fecha_inicio and fecha_fin):
             error = "Por favor, completa todos los campos."
        else:
            try:
                ini = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
                if ini > fin:
                    error = "La fecha de inicio no puede ser posterior a la fin."
                else:
                    resultado, error = obtener_horas(modelo, fecha_inicio, fecha_fin, sitio)
            except ValueError:
                error = "Formato de fecha no válido."
        
        context["resultado"] = resultado
        context["error"] = error

    return render_template("index.html", **context)

if __name__ == "__main__":
    # Render usa el puerto que le asigne el sistema
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
