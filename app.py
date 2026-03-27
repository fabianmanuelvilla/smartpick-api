from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math
import json
import urllib.request
import ssl
import threading
import time
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# --- 1. CACHÉ Y VARIABLES GLOBALES ---
jackpot_cache = {
    "powerball": {"jackpot": "Loading...", "drawDate": "", "numbers": [], "last_updated": None},
    "mega_millions": {"jackpot": "Loading...", "drawDate": "", "numbers": [], "last_updated": None}
}

# Seguridad: Lee la key del entorno del servidor, o usa la tuya por defecto
API_KEY = os.environ.get("APIVERVE_KEY", "apv_0ad9c4e9-f30e-43ad-888a-8a85f5db7825")
API_URLS = {
    "powerball": "https://api.apiverve.com/v1/lottery?numbers=powerball",
    "mega_millions": "https://api.apiverve.com/v1/lottery?numbers=mega_millions"
}

# --- 2. TAREAS EN BACKGROUND (CRON JOB INTERNO) ---
def fetch_jackpot_from_api(loteria):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            API_URLS[loteria],
            headers={"User-Agent": "SmartPickApp/3.4", "x-api-key": API_KEY}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "ok":
                jackpot_cache[loteria] = {
                    "jackpot": data["data"].get("jackpot", "N/A"),
                    "drawDate": data["data"].get("drawDate", ""),
                    "numbers": data["data"].get("numbers", []),
                    "last_updated": datetime.utcnow().isoformat()
                }
                print(f"[CACHE] {loteria} actualizado: {jackpot_cache[loteria]['jackpot']}")
    except Exception as e:
        print(f"[CACHE ERROR] {loteria}: {e}")

def refresh_all_jackpots():
    print("[CRON] Actualizando jackpots desde ApiVerve...")
    for loteria in API_URLS:
        fetch_jackpot_from_api(loteria)
        time.sleep(2) # Pausa táctica para no saturar la API

def cron_job():
    refresh_all_jackpots()
    while True:
        time.sleep(6 * 60 * 60)  # Duerme por 6 horas exactas
        refresh_all_jackpots()

# Inicia el hilo silencioso al arrancar el servidor
threading.Thread(target=cron_job, daemon=True).start()

# --- 3. CONFIGURACIÓN DEL MOTOR GAUSSIANO ---
LOTERIAS = {
    "powerball": {
        "numeros": {"total": 69, "elegir": 5},
        "especial": {"total": 26, "nombre": "powerball"},
        "media": 175.0,
        "std": 38.0,
    },
    "mega_millions": {
        "numeros": {"total": 70, "elegir": 5},
        "especial": {"total": 25, "nombre": "mega_ball"},
        "media": 177.0,
        "std": 39.0,
    }
}

PESOS_BASE = {n: 1.0 for n in range(1, 71)}
for n in [13, 47]: PESOS_BASE[n] = 0.90 # Micro-castigo estadístico

PRIMOS_VALIDOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67}
FIBONACCI_VALIDOS = {1, 2, 3, 5, 8, 13, 21, 34, 55}

def calcular_temperatura(suma, media, std):
    distancia = abs(suma - media)
    if distancia <= std * 0.5: return "ZONA ROJA — Núcleo Probable"
    elif distancia <= std: return "ZONA NARANJA — Estándar"
    elif distancia <= std * 1.5: return "ZONA AMARILLA — Dispersión"
    else: return "ZONA AZUL — Extremo/Raro"

def generar_prediccion(config):
    total = config["numeros"]["total"]
    elegir = config["numeros"]["elegir"]
    media = config["media"]
    std = config["std"]
    population = list(range(1, total + 1))
    weights = [PESOS_BASE.get(n, 1.0) for n in population]
    
    intentos = 0
    while intentos < 10000:
        intentos += 1
        candidata_set = set()
        while len(candidata_set) < elegir:
            bola = random.choices(population, weights=weights, k=1)[0]
            candidata_set.add(bola)
        candidata = sorted(list(candidata_set))
        suma = sum(candidata)
        
        if not (media - std * 2 <= suma <= media + std * 2): continue
        impares = sum(1 for n in candidata if n % 2 != 0)
        if impares == 0 or impares == elegir: continue
        consecutivos = sum(1 for i in range(len(candidata) - 1) if candidata[i+1] == candidata[i] + 1)
        if consecutivos > 1: continue
        
        Z = (suma - media) / std
        prob = math.exp(-0.5 * (Z ** 2))
        if random.random() > prob: continue
        
        ceros = sum(1 for n in candidata if n % 10 == 0)
        if ceros > 1: continue
        decadas = [n // 10 for n in candidata]
        if any(decadas.count(d) > 2 for d in set(decadas)): continue
        fibs = sum(1 for n in candidata if n in FIBONACCI_VALIDOS)
        if fibs > 2: continue
        primos = sum(1 for n in candidata if n in PRIMOS_VALIDOS)
        if not (1 <= primos <= 3): continue
        
        especial = random.randint(1, config["especial"]["total"])
        
        return {
            "numeros": candidata,
            config["especial"]["nombre"]: especial,
            "suma": suma,
            "temperatura": calcular_temperatura(suma, media, std),
            "pureza_gauss": int(prob * 100),
            "intentos": intentos,
            "auditoria": {
                "primos": primos,
                "fibonacci": fibs,
                "consecutivos": consecutivos,
                "ceros": ceros,
                "paridad": f"Impares: {impares} / Pares: {elegir - impares}"
            }
        }
    return None

# --- 4. ENDPOINTS API REST ---
@app.route("/")
def index():
    return jsonify({
        "engine": "SmartPick AI Core",
        "status": "online",
        "version": "3.4 — Production Ready",
        "cache_status": {
            "powerball": jackpot_cache["powerball"]["last_updated"],
            "mega_millions": jackpot_cache["mega_millions"]["last_updated"]
        },
        "endpoints": ["/predict/<loteria>", "/jackpot/<loteria>", "/ping"]
    })

# NUEVO: Endpoint Anti-Sleep para Render
@app.route("/ping")
def ping():
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Servidor despierto y caché protegido."
    })

@app.route("/jackpot/<loteria>")
def jackpot(loteria):
    loteria = loteria.lower().replace("-", "_")
    if loteria not in jackpot_cache:
        return jsonify({"error": "Lotería no encontrada. Usa: powerball, mega_millions"}), 404
    cache = jackpot_cache[loteria]
    return jsonify({
        "status": "ok",
        "source": "cache",
        "last_updated": cache["last_updated"],
        "data": {
            "jackpot": cache["jackpot"],
            "drawDate": cache["drawDate"],
            "numbers": cache["numbers"]
        }
    })

@app.route("/jackpot/refresh")
def refresh_cache():
    refresh_all_jackpots()
    return jsonify({"status": "ok", "message": "Caché actualizado manualmente", "data": jackpot_cache})

@app.route("/predict/<loteria>")
def predict(loteria):
    loteria = loteria.lower().replace("-", "_")
    if loteria not in LOTERIAS:
        return jsonify({"error": "Lotería no encontrada. Usa: powerball, mega_millions"}), 404
    cantidad = min(int(request.args.get("cantidad", 1)), 10)
    config = LOTERIAS[loteria]
    resultados = [generar_prediccion(config) for _ in range(cantidad)]
    return jsonify({
        "loteria": loteria,
        "predicciones": [r for r in resultados if r],
        "modelo": "Thermodynamic Engine v3.4"
    })

if __name__ == "__main__":
    app.run(debug=True)