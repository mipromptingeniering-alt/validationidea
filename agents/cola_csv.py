import os
import csv
import json
from datetime import datetime

COLA_PATH = os.path.join("data", "cola_pendiente.csv")
CAMPOS = ["timestamp", "nombre_idea", "motivo_fallo", "intentos", "datos_json"]


def _asegurar_archivo():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(COLA_PATH):
        with open(COLA_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS)
            writer.writeheader()


def guardar_en_cola(nombre_idea, motivo_fallo, datos_json):
    _asegurar_archivo()
    fila = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nombre_idea": str(nombre_idea)[:200],
        "motivo_fallo": str(motivo_fallo)[:500],
        "intentos": "1",
        "datos_json": json.dumps(datos_json, ensure_ascii=False)
    }
    with open(COLA_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writerow(fila)
    print(f"📋 '{nombre_idea}' guardada en cola CSV para reintento")


def obtener_pendientes():
    _asegurar_archivo()
    pendientes = []
    with open(COLA_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            try:
                if int(fila.get("intentos", 0)) < 3:
                    pendientes.append(dict(fila))
            except (ValueError, KeyError):
                continue
    return pendientes


def incrementar_intentos(timestamp):
    _asegurar_archivo()
    filas = []
    with open(COLA_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = list(reader)
    for fila in filas:
        if fila.get("timestamp") == timestamp:
            fila["intentos"] = str(int(fila.get("intentos", 1)) + 1)
    with open(COLA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(filas)


def eliminar_de_cola(timestamp):
    _asegurar_archivo()
    filas = []
    with open(COLA_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = [row for row in reader if row.get("timestamp") != timestamp]
    with open(COLA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(filas)


def contar_pendientes():
    return len(obtener_pendientes())
