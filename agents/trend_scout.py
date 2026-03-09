import os
import json
import time
import requests
from datetime import datetime, timedelta

RUTA_TENDENCIAS = "data/tendencias.json"
os.makedirs("data", exist_ok=True)

# TTL por fuente (horas)
TTL = {
    "hackernews":  2,
    "github":      6,
    "reddit":      4,
    "producthunt": 12,
    "curada":      24,
}

def _cache_valida(datos: dict, fuente: str) -> bool:
    ts = datos.get("timestamps", {}).get(fuente)
    if not ts:
        return False
    limite = datetime.fromisoformat(ts) + timedelta(hours=TTL.get(fuente, 6))
    return datetime.now() < limite

def _cargar_cache() -> dict:
    if os.path.exists(RUTA_TENDENCIAS):
        try:
            with open(RUTA_TENDENCIAS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"tendencias_por_fuente": {}, "timestamps": {}, "tendencias": []}

def _guardar_cache(datos: dict):
    try:
        with open(RUTA_TENDENCIAS, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Error guardando tendencias: {e}")

# ════════════════════════════════════════════════════════
#  SCRAPERS
# ════════════════════════════════════════════════════════
def _scrape_hackernews() -> list:
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=8
        ).json()[:20]
        titulos = []
        for item_id in ids[:12]:
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5
                ).json()
                t = item.get("title", "")
                if t and len(t) > 10:
                    titulos.append(f"[HN] {t}")
            except:
                pass
            time.sleep(0.1)
        print(f"  ✅ HackerNews: {len(titulos)} items")
        return titulos
    except Exception as e:
        print(f"  ⚠️ HackerNews: {e}")
        return []

def _scrape_github() -> list:
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": "created:>2026-01-01", "sort": "stars", "order": "desc", "per_page": 15},
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        resultado = []
        for r in resp.json().get("items", []):
            desc     = r.get("description", "") or ""
            estrellas = r.get("stargazers_count", 0)
            temas    = r.get("topics", [])
            if desc and len(desc) > 10:
                resultado.append(
                    f"[GitHub⭐{estrellas}] {r.get('full_name','')}: {desc[:120]}"
                    + (f" [{','.join(temas[:3])}]" if temas else "")
                )
        print(f"  ✅ GitHub: {len(resultado)} repos")
        return resultado[:10]
    except Exception as e:
        print(f"  ⚠️ GitHub: {e}")
        return []

def _scrape_reddit() -> list:
    resultados = []
    headers    = {"User-Agent": "ValidationIdea/2.0"}
    for sub in ["SideProject", "entrepreneur", "artificial"]:
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=10",
                headers=headers, timeout=8
            )
            if resp.status_code != 200:
                continue
            for post in resp.json().get("data", {}).get("children", []):
                d = post.get("data", {})
                t = d.get("title", "")
                s = d.get("score", 0)
                if t and len(t) > 15 and s > 10:
                    resultados.append(f"[r/{sub} 🔥{s}] {t[:140]}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️ r/{sub}: {e}")
    print(f"  ✅ Reddit: {len(resultados)} posts")
    return resultados[:12]

def _scrape_producthunt() -> list:
    # Intento via RSS
    try:
        resp = requests.get(
            "https://www.producthunt.com/feed",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
        if resp.status_code == 200:
            import re
            titulos = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", resp.text)
            resultado = [f"[PH] {t[:140]}" for t in titulos[1:12] if len(t) > 10]
            print(f"  ✅ ProductHunt RSS: {len(resultado)} productos")
            return resultado
    except Exception as e:
        print(f"  ⚠️ ProductHunt: {e}")
    return []

def _curada_ia() -> list:
    """Lista curada de herramientas y tendencias IA — actualizada a marzo 2026."""
    return [
        "[AI Trend] Agentes IA autónomos (LangGraph, CrewAI) ejecutan tareas largas sin intervención",
        "[AI Trend] Vídeo generativo: Sora, Runway Gen-3, Kling AI — coste bajando agresivamente",
        "[AI Trend] Voice cloning hiperrealista: ElevenLabs, Cartesia — coste casi 0",
        "[AI Trend] Bolt.new / Lovable: apps completas desde un prompt — no-code IA masivo",
        "[AI Trend] Modelos locales (Ollama, LM Studio) en laptop — privacidad sin API",
        "[AI Trend] n8n + IA: automatización de workflows empresariales sin código",
        "[AI Trend] NotebookLM: análisis de documentos y podcasts con IA",
        "[AI Trend] Dify: plataforma open-source para apps RAG + agentes IA",
        "[AI Trend] Cursor + Claude: devs 3x más rápidos construyendo productos",
        "[AI Trend] MCP (Model Context Protocol) Anthropic — integración universal de herramientas",
        "[AI Trend] Browser agents (Notte, Browserbase) — automatización web a escala",
        "[AI Trend] Vibe coding: no-code + IA para construir SaaS por no programadores",
        "[AI Trend] AI wrappers rentables: interfaces simples sobre APIs con nicho muy específico",
        "[AI Trend] TestSprite: QA automático generado por IA sin equipo de testing",
        "[AI Trend] Accent Conversion (Krisp) — eliminación de acento en llamadas",
        "[AI Trend] OpenHands: agente que escribe y ejecuta código solo (28k⭐ GitHub)",
        "[AI Trend] microsoft/markitdown: convierte cualquier archivo a Markdown (50k⭐)",
        "[AI Trend] browser-use: controla el navegador con IA (35k⭐)",
        "[AI Trend] Qwen3.5 Small — LLM potente que corre en local en cualquier máquina",
        "[Mercado] Empresas PYME buscan reemplazar SaaS caro con alternativas IA propias",
        "[Mercado] Creadores de contenido necesitan herramientas de personalización masiva",
        "[Mercado] Consultores y freelancers buscan automatizar reportes y propuestas",
        "[Mercado] E-commerce pequeño necesita IA de atención al cliente sin coste de Intercom",
    ]

# ════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL CON TTL
# ════════════════════════════════════════════════════════
def actualizar_tendencias() -> list:
    datos = _cargar_cache()
    por_fuente = datos.get("tendencias_por_fuente", {})
    timestamps = datos.get("timestamps", {})
    ahora      = datetime.now().isoformat()

    # Solo actualizar fuentes cuyo TTL ha expirado
    if not _cache_valida(datos, "hackernews"):
        por_fuente["hackernews"] = _scrape_hackernews()
        timestamps["hackernews"] = ahora
        print(f"  🔄 HackerNews actualizado")
    else:
        print(f"  ⏭️ HackerNews en cache ({len(por_fuente.get('hackernews',[]))} items)")

    if not _cache_valida(datos, "github"):
        por_fuente["github"] = _scrape_github()
        timestamps["github"] = ahora
        print(f"  🔄 GitHub actualizado")
    else:
        print(f"  ⏭️ GitHub en cache")

    if not _cache_valida(datos, "reddit"):
        por_fuente["reddit"] = _scrape_reddit()
        timestamps["reddit"] = ahora
        print(f"  🔄 Reddit actualizado")
    else:
        print(f"  ⏭️ Reddit en cache")

    if not _cache_valida(datos, "producthunt"):
        por_fuente["producthunt"] = _scrape_producthunt()
        timestamps["producthunt"] = ahora
        print(f"  🔄 ProductHunt actualizado")
    else:
        print(f"  ⏭️ ProductHunt en cache")

    if not _cache_valida(datos, "curada"):
        por_fuente["curada"] = _curada_ia()
        timestamps["curada"] = ahora
        print(f"  🔄 Lista curada IA actualizada")
    else:
        print(f"  ⏭️ Lista curada en cache")

    # Unir todas sin duplicados
    todas  = []
    vistas = set()
    for fuente in ["hackernews", "github", "reddit", "producthunt", "curada"]:
        for t in por_fuente.get(fuente, []):
            clave = t[:60].lower()
            if clave not in vistas:
                vistas.add(clave)
                todas.append(t)

    datos = {
        "tendencias_por_fuente": por_fuente,
        "timestamps":            timestamps,
        "tendencias":            todas,
        "total":                 len(todas),
        "ultima_actualizacion":  ahora,
    }
    _guardar_cache(datos)
    print(f"✅ {len(todas)} tendencias disponibles (con TTL cache)")
    return todas

def get_tendencias() -> list:
    datos = _cargar_cache()
    return datos.get("tendencias", []) or actualizar_tendencias()

# aqui finaliza el codigo de agents/trend_scout.py
