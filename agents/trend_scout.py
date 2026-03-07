# agents/trend_scout.py
import requests, json
from datetime import datetime

def obtener_tendencias():
    """
    Fuentes gratuitas de tendencias sin API key:
    - HackerNews top stories
    - Product Hunt via RSS
    """
    tendencias = []
    
    # HackerNews API (gratis, sin auth)
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        )
        ids = resp.json()[:10]
        for item_id in ids[:5]:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                timeout=5
            ).json()
            if item and item.get("type") == "story":
                tendencias.append(item.get("title", ""))
    except:
        pass
    
    # Guardar en KB
    if tendencias:
        try:
            with open("data/tendencias.json", "w", encoding="utf-8") as f:
                json.dump({
                    "fecha": datetime.now().isoformat(),
                    "tendencias": tendencias
                }, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    return tendencias[:8]

def get_tendencias_guardadas():
    try:
        with open("data/tendencias.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tendencias", [])
    except:
        return []
