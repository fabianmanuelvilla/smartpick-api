from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math
import json
import urllib.request
import ssl

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE LOTERÍAS ---
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
for n in [13, 47]: PESOS_BASE[n] = 0.90

PRIMOS_VALIDOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67}
FIBONACCI_VALIDOS = {1, 2, 3, 5, 8, 13, 21, 34, 55}

# --- FUNCIONES CORE ---
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

# --- ENDPOINTS REST API ---
@app.route("/")
def index():
    return jsonify({
        "engine": "SmartPick AI Core",
        "status": "online",
        "version": "3.2",
        "endpoints": ["/predict/powerball", "/predict/mega_millions", "/jackpot/powerball", "/jackpot/mega_millions"]
    })

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
        "modelo": "Thermodynamic Engine v3.2"
    })

@app.route("/jackpot/<loteria>")
def jackpot(loteria):
    loteria = loteria.lower().replace("-", "_")
    urls = {
        "powerball": "https://api.apiverve.com/v1/lottery?numbers=powerball",
        "mega_millions": "https://api.apiverve.com/v1/lottery?numbers=mega_millions"
    }
    if loteria not in urls:
        return jsonify({"error": "Lotería no encontrada"}), 404
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            urls[loteria],
            headers={"User-Agent": "SmartPickApp/3.2"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "jackpot": "N/A"}), 500

if __name__ == "__main__":
    app.run(debug=True)