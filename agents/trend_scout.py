import requests, json, os
from datetime import datetime

TENDENCIAS_PATH = "data/tendencias.json"

def actualizar_tendencias():
    tendencias = []
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=8
        ).json()[:15]
        for item_id in ids[:8]:
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                    timeout=5
                ).json()
                if item and item.get("title"):
                    tendencias.append(item["title"])
            except:
                pass
    except Exception as e:
        print(f"⚠️ HN fetch error: {e}")

    if tendencias:
        os.makedirs("data", exist_ok=True)
        with open(TENDENCIAS_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "fecha":      datetime.now().isoformat(),
                "tendencias": tendencias
            }, f, ensure_ascii=False, indent=2)
        print(f"🌐 {len(tendencias)} tendencias actualizadas")

    return tendencias

def get_tendencias():
    try:
        if os.path.exists(TENDENCIAS_PATH):
            with open(TENDENCIAS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("tendencias", [])
    except:
        pass
    return actualizar_tendencias()
