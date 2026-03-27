from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math

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

# --- CONSTANTES MATEMÁTICAS Y TERMODINÁMICAS ---
PESOS_BASE = {n: 1.0 for n in range(1, 71)}
# Micro-castigo a números históricamente anómalos (opcional basado en tu análisis)
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
        
        # 1. Generación Base
        candidata_set = set()
        while len(candidata_set) < elegir:
            bola = random.choices(population, weights=weights, k=1)[0]
            candidata_set.add(bola)
        candidata = sorted(list(candidata_set))
        suma = sum(candidata)
        
        # 2. Límites Duros de Suma
        if not (media - std * 2 <= suma <= media + std * 2): continue
        
        # 3. Paridad (No todos pares ni todos impares)
        impares = sum(1 for n in candidata if n % 2 != 0)
        if impares == 0 or impares == elegir: continue
        
        # 4. Consecutivos (Máximo 1 pareja)
        consecutivos = sum(1 for i in range(len(candidata) - 1) if candidata[i+1] == candidata[i] + 1)
        if consecutivos > 1: continue
        
        # 5. Gravedad Gaussiana (Muestreo de Rechazo)
        Z = (suma - media) / std
        prob = math.exp(-0.5 * (Z ** 2))
        if random.random() > prob: continue
        
        # --- 6. HIGIENE ESTRUCTURAL PROFUNDA ---
        
        # Anti-Cero (Máximo 1 número terminado en 0)
        ceros = sum(1 for n in candidata if n % 10 == 0)
        if ceros > 1: continue

        # Densidad de Décadas (Máximo 2 números en la misma decena)
        decadas = [n // 10 for n in candidata]
        if any(decadas.count(d) > 2 for d in set(decadas)): continue

        # Filtro Fibonacci (Máximo 2)
        fibs = sum(1 for n in candidata if n in FIBONACCI_VALIDOS)
        if fibs > 2: continue

        # Proporción de Primos (Entre 1 y 3 para juegos de 5 bolas)
        primos = sum(1 for n in candidata if n in PRIMOS_VALIDOS)
        if not (1 <= primos <= 3): continue
        
        # --- FIN HIGIENE ESTRUCTURAL ---

        # 7. Bola Especial (Powerball / Mega Ball) al azar puro
        especial = random.randint(1, config["especial"]["total"])
        
        # 8. Retorno del JSON Formateado para Flutterflow
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
        "version": "3.1 (Production Ready)",
        "endpoints": ["/predict/powerball", "/predict/mega_millions"]
    })

@app.route("/predict/<loteria>")
def predict(loteria):
    loteria = loteria.lower().replace("-", "_")
    if loteria not in LOTERIAS:
        return jsonify({"error": "Lotería no encontrada. Usa: powerball, mega_millions"}), 404
        
    cantidad = min(int(request.args.get("cantidad", 1)), 10) # Límite de 10 por llamada de API
    config = LOTERIAS[loteria]
    
    resultados = [generar_prediccion(config) for _ in range(cantidad)]
    
    return jsonify({
        "loteria": loteria,
        "predicciones": [r for r in resultados if r],
        "modelo": "Thermodynamic Engine v3.1"
    })

if __name__ == "__main__":
    app.run(debug=True)