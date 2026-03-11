"""
trend_scout.py - Obtiene tendencias tech reales de fuentes publicas
"""
import os, json, time, urllib.request, urllib.parse
from datetime import datetime, timedelta

TRENDS_FILE    = "data/tendencias.json"
CACHE_MINUTOS  = 120

FUENTES_RSS = [
    ("HackerNews Top",  "https://hnrss.org/frontpage?count=10"),
    ("GitHub Trending", "https://github.com/trending/python?since=daily"),
]

TENDENCIAS_FALLBACK = [
    "LLM agents con memoria persistente - 2026",
    "RAG pipelines para empresas medianas",
    "Automatizacion de flujos con n8n + IA",
    "Voice AI para atencion al cliente B2B",
    "AI code review automatico para equipos",
    "Computer vision para control de calidad industrial",
    "Fine-tuning modelos pequenos para nicho especifico",
    "AI legal document analysis para PYMEs",
    "Predictive analytics para churn SaaS",
    "Multi-agent systems para automatizacion de ventas",
    "Embeddings para busqueda semantica en docs privados",
    "AI onboarding personalizado para SaaS B2B",
]

def _load_cache():
    try:
        with open(TRENDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"tendencias": [], "ultima_actualizacion": ""}

def _save_cache(d):
    os.makedirs("data", exist_ok=True)
    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _cache_valido():
    cache = _load_cache()
    if not cache.get("tendencias") or not cache.get("ultima_actualizacion"):
        return False
    try:
        ultima = datetime.fromisoformat(cache["ultima_actualizacion"])
        return datetime.now() - ultima < timedelta(minutes=CACHE_MINUTOS)
    except:
        return False

def _fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 ValidationIdea/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"   fetch {url[:50]}: {e}")
        return ""

def _extraer_titulos_rss(xml_text):
    import re
    titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', xml_text)
    if not titulos:
        titulos = re.findall(r'<title>(.*?)</title>', xml_text)
    return [t.strip() for t in titulos if len(t.strip()) > 10][:8]

def _scrape_hackernews():
    trends = []
    try:
        html = _fetch_url("https://news.ycombinator.com/")
        if html:
            import re
            titulos = re.findall(r'class="titleline"[^>]*><a[^>]*>(.*?)</a>', html)
            tech_kw = ["ai","llm","gpt","api","saas","startup","open source","tool",
                       "launch","new","python","cloud","agent","model","automation"]
            for t in titulos[:20]:
                tl = t.lower()
                if any(k in tl for k in tech_kw):
                    trends.append(f"HN: {t.strip()[:100]}")
                if len(trends) >= 5:
                    break
    except Exception as e:
        print(f"   HN scrape: {e}")
    return trends

def _scrape_reddit_machinelearning():
    trends = []
    try:
        url  = "https://www.reddit.com/r/MachineLearning/hot.json?limit=10"
        html = _fetch_url(url)
        if html:
            data  = json.loads(html)
            posts = data.get("data",{}).get("children",[])
            for p in posts[:6]:
                titulo = p.get("data",{}).get("title","")
                if titulo and len(titulo) > 15:
                    trends.append(f"Reddit ML: {titulo[:100]}")
    except Exception as e:
        print(f"   Reddit ML: {e}")
    return trends

def _scrape_producthunt():
    trends = []
    try:
        html = _fetch_url("https://www.producthunt.com/")
        if html:
            import re
            titulos = re.findall(r'"name":"([^"]{10,80})"', html)
            vistos  = set()
            for t in titulos[:20]:
                if t not in vistos and "Product Hunt" not in t:
                    trends.append(f"PH: {t}")
                    vistos.add(t)
                if len(trends) >= 4:
                    break
    except Exception as e:
        print(f"   PH: {e}")
    return trends

def actualizar_tendencias():
    if _cache_valido():
        print("✅ Tendencias en cache (valido)")
        return

    print("🌐 Actualizando tendencias...")
    todas = []

    hn = _scrape_hackernews()
    todas.extend(hn)
    print(f"   HN: {len(hn)} trends")

    reddit = _scrape_reddit_machinelearning()
    todas.extend(reddit)
    print(f"   Reddit: {len(reddit)} trends")

    ph = _scrape_producthunt()
    todas.extend(ph)
    print(f"   PH: {len(ph)} trends")

    if not todas or len(todas) < 5:
        print("   Usando fallback")
        todas = TENDENCIAS_FALLBACK[:]

    cache = {
        "tendencias":            todas[:20],
        "ultima_actualizacion":  datetime.now().isoformat(),
        "fuentes":               ["HackerNews","Reddit ML","ProductHunt"],
    }
    _save_cache(cache)
    print(f"✅ {len(todas)} tendencias guardadas")

def get_tendencias():
    cache = _load_cache()
    tends = cache.get("tendencias", [])
    if not tends:
        return TENDENCIAS_FALLBACK[:]
    return tends

# fin agents/trend_scout.py
