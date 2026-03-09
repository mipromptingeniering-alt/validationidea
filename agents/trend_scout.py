import os
import json
import time
import requests
from datetime import datetime

RUTA_TENDENCIAS = "data/tendencias.json"
os.makedirs("data", exist_ok=True)

# ════════════════════════════════════════════════════════
#  FUENTES DE INSPIRACIÓN
# ════════════════════════════════════════════════════════

def _scrape_hackernews() -> list:
    """Top stories de HackerNews — lo que leen los devs ahora."""
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=8
        ).json()[:20]
        titulos = []
        for item_id in ids[:12]:
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                    timeout=5
                ).json()
                titulo = item.get("title", "")
                if titulo and len(titulo) > 10:
                    titulos.append(f"[HN] {titulo}")
            except:
                pass
            time.sleep(0.1)
        print(f"  ✅ HackerNews: {len(titulos)} items")
        return titulos
    except Exception as e:
        print(f"  ⚠️ HackerNews: {e}")
        return []

def _scrape_github_trending() -> list:
    """Repositorios trending en GitHub — lo que la gente construye."""
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": "created:>2026-02-01",
                "sort": "stars",
                "order": "desc",
                "per_page": 15
            },
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        repos = resp.json().get("items", [])
        resultados = []
        for r in repos:
            nombre      = r.get("full_name", "")
            descripcion = r.get("description", "") or ""
            estrellas   = r.get("stargazers_count", 0)
            temas       = r.get("topics", [])
            if descripcion and len(descripcion) > 10:
                resultados.append(
                    f"[GitHub⭐{estrellas}] {nombre}: {descripcion[:120]}"
                    + (f" [{', '.join(temas[:3])}]" if temas else "")
                )
        print(f"  ✅ GitHub Trending: {len(resultados)} repos")
        return resultados[:10]
    except Exception as e:
        print(f"  ⚠️ GitHub Trending: {e}")
        return []

def _scrape_reddit_sideproject() -> list:
    """Posts recientes de r/SideProject y r/entrepreneur — ideas reales que la gente construye."""
    resultados = []
    subreddits = ["SideProject", "entrepreneur", "indiehackers"]
    headers    = {"User-Agent": "ValidationIdea/2.0 (trend scout)"}
    for sub in subreddits:
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=10",
                headers=headers,
                timeout=8
            )
            if resp.status_code != 200:
                continue
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                data   = post.get("data", {})
                titulo = data.get("title", "")
                score  = data.get("score", 0)
                if titulo and len(titulo) > 15 and score > 10:
                    resultados.append(f"[r/{sub} 🔥{score}] {titulo[:140]}")
            print(f"  ✅ r/{sub}: {len(posts)} posts")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️ r/{sub}: {e}")
    return resultados[:12]

def _scrape_producthunt() -> list:
    """Productos trending en ProductHunt — herramientas de IA que la gente lanza."""
    try:
        # Usamos la API pública sin autenticación (posts recientes)
        resp = requests.get(
            "https://www.producthunt.com/frontend/graphql",
            json={
                "query": """
                {
                  posts(order: RANKING, first: 20) {
                    edges {
                      node {
                        name
                        tagline
                        votesCount
                        topics { edges { node { name } } }
                      }
                    }
                  }
                }
                """
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )
        if resp.status_code == 200:
            edges = resp.json().get("data", {}).get("posts", {}).get("edges", [])
            resultados = []
            for e in edges:
                node    = e.get("node", {})
                nombre  = node.get("name", "")
                tagline = node.get("tagline", "")
                votos   = node.get("votesCount", 0)
                topics  = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
                if nombre and tagline:
                    resultados.append(
                        f"[PH 👍{votos}] {nombre}: {tagline[:100]}"
                        + (f" [{', '.join(topics[:2])}]" if topics else "")
                    )
            if resultados:
                print(f"  ✅ ProductHunt GraphQL: {len(resultados)} productos")
                return resultados[:10]
    except Exception as e:
        print(f"  ⚠️ ProductHunt GraphQL: {e}")

    # Fallback: RSS de ProductHunt
    try:
        resp = requests.get(
            "https://www.producthunt.com/feed",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
        if resp.status_code == 200:
            import re
            titulos = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", resp.text)
            resultados = [f"[PH] {t[:140]}" for t in titulos[1:12] if len(t) > 10]
            print(f"  ✅ ProductHunt RSS: {len(resultados)} productos")
            return resultados
    except Exception as e:
        print(f"  ⚠️ ProductHunt RSS: {e}")
    return []

def _scrape_ai_tools_curados() -> list:
    """Lista curada de herramientas y tendencias IA de marzo 2026 — siempre fresca."""
    # Fuentes verificadas de búsqueda web — actualiza esta lista mensualmente
    return [
        "[AI Trend] Agentes IA autónomos que ejecutan tareas largas sin intervención humana (LangGraph, CrewAI)",
        "[AI Trend] Generación de vídeo a partir de texto: Sora, Runway Gen-3, Kling AI — mercado explotando",
        "[AI Trend] Voice cloning + text-to-speech hiperrealista: ElevenLabs, Cartesia — coste cayendo a 0",
        "[AI Trend] Bolt.new y Lovable: apps completas generadas desde un prompt — no-code IA masivo",
        "[AI Trend] Modelos locales en laptop (Ollama, LM Studio) — privacidad sin coste de API",
        "[AI Trend] n8n + IA: automatización de workflows empresariales sin código — explosión en PYMES",
        "[AI Trend] NotebookLM: análisis de documentos y podcasts IA — educación y consultoría",
        "[AI Trend] Dify: plataforma open source para crear apps con RAG y agentes IA",
        "[AI Trend] Cursor + Claude: desarrollo de software por IA — devs 3x más rápidos",
        "[AI Trend] MCP (Model Context Protocol) de Anthropic — integración universal de herramientas con IA",
        "[AI Trend] Accent Conversion de Krisp — eliminación de acento en llamadas de trabajo",
        "[AI Trend] Browser agents (Notte, Browserbase) — automatización web a escala con IA",
        "[AI Trend] Vibe coding: no-code + IA para construir SaaS por no programadores",
        "[AI Trend] AI wrappers rentables: interfaces simples sobre APIs de IA con nicho muy específico",
        "[AI Trend] TestSprite: testing automático de apps generado por IA — QA sin equipo",
        "[GitHub] microsoft/markitdown — convierte cualquier archivo a Markdown con IA (50k⭐)",
        "[GitHub] browser-use — controla el navegador con IA de forma autónoma (35k⭐)",
        "[GitHub] OpenHands — agente IA que escribe y ejecuta código solo (28k⭐)",
        "[GitHub] Qwen3.5 Small — LLM potente que corre en local en cualquier máquina",
        "[PH Viral] Gojiberry AI — targeting de compradores en modo compra con IA",
        "[PH Viral] Aident AI — automatizaciones en lenguaje natural sin workflows",
        "[PH Viral] Voicr — clonación de voz profesional para creadores de contenido",
    ]

# ════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ════════════════════════════════════════════════════════
def actualizar_tendencias() -> list:
    """Recopila tendencias de todas las fuentes y las guarda."""
    print("🌐 Actualizando tendencias desde múltiples fuentes...")
    todas = []

    # 1. HackerNews
    todas += _scrape_hackernews()

    # 2. GitHub Trending
    todas += _scrape_github_trending()

    # 3. Reddit
    todas += _scrape_reddit_sideproject()

    # 4. ProductHunt
    todas += _scrape_producthunt()

    # 5. Lista curada IA 2026
    todas += _scrape_ai_tools_curados()

    # Eliminar duplicados manteniendo orden
    vistas    = set()
    unicas    = []
    for t in todas:
        clave = t[:60].lower()
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(t)

    print(f"✅ {len(unicas)} tendencias únicas recopiladas")

    try:
        with open(RUTA_TENDENCIAS, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp":   datetime.now().isoformat(),
                "tendencias":  unicas,
                "fuentes":     ["HackerNews", "GitHub", "Reddit", "ProductHunt", "CuradaIA2026"],
                "total":       len(unicas)
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Error guardando tendencias: {e}")

    return unicas

def get_tendencias() -> list:
    """Devuelve las tendencias guardadas, o las actualiza si no existen."""
    try:
        if os.path.exists(RUTA_TENDENCIAS):
            with open(RUTA_TENDENCIAS, "r", encoding="utf-8") as f:
                datos = json.load(f)
            return datos.get("tendencias", [])
    except Exception as e:
        print(f"⚠️ Error leyendo tendencias: {e}")
    return actualizar_tendencias()

# aqui finaliza el codigo de agents/trend_scout.py
