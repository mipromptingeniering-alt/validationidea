"""
market_validator.py
Valida ideas con datos reales GRATUITOS:
- Google Trends (pytrends)
- Reddit search
- GitHub search (señal técnica)
Devuelve score_real y evidencias para enriquecer el score final.
"""
import time
import requests

def _google_trends(keywords: list) -> dict:
    """Retorna interés relativo 0-100 de los últimos 12 meses."""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="es-ES", tz=60, timeout=(10, 25))
        kw = [k[:100] for k in keywords[:3]]
        pt.build_payload(kw, timeframe="today 12-m", geo="")
        data = pt.interest_over_time()
        if data.empty:
            return {}
        return {col: int(data[col].mean()) for col in data.columns if col != "isPartial"}
    except Exception as e:
        return {"error": str(e)[:80]}

def _reddit_evidencia(problema: str) -> dict:
    """Busca posts en Reddit que hablen del problema."""
    try:
        headers = {"User-Agent": "ValidationIdea/3.0"}
        import re as _re
        palabras = _re.sub(r"[^a-zA-Z0-9 ]","",problema[:60].replace("helio","helium").replace("escasez","shortage").replace("cadena de suministro","supply chain"))
        query    = " ".join(palabras.split()[:6])
        resp    = requests.get(
            f"https://www.reddit.com/search.json?q={query}+startup+SaaS&sort=relevance&t=month&limit=10&type=link",
            headers=headers, timeout=8
        )
        if resp.status_code != 200:
            return {"posts": 0, "upvotes_total": 0}
        posts     = resp.json().get("data", {}).get("children", [])
        upvotes   = sum(p["data"].get("score", 0) for p in posts)
        subs_list = list(set(p["data"].get("subreddit","") for p in posts[:5]))
        return {
            "posts":         len(posts),
            "upvotes_total": upvotes,
            "subreddits":    subs_list[:4],
            "top_post":      posts[0]["data"].get("title","")[:120] if posts else ""
        }
    except Exception as e:
        return {"posts": 0, "upvotes_total": 0, "error": str(e)[:80]}

def _github_demanda(nombre: str, tags: list) -> dict:
    """Repositorios existentes como señal de demanda técnica."""
    try:
        query = " ".join([nombre] + tags[:2])
        resp  = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query[:100], "sort":"stars","order":"desc","per_page":5},
            headers={"Accept":"application/vnd.github.v3+json"},
            timeout=8
        )
        if resp.status_code != 200:
            return {"repos": 0}
        items = resp.json().get("items", [])
        total = resp.json().get("total_count", 0)
        return {
            "repos":          total,
            "top_repo_stars": items[0].get("stargazers_count",0) if items else 0,
            "top_repo":       items[0].get("full_name","") if items else "",
            "señal":          "alta" if total > 50 else "media" if total > 10 else "baja"
        }
    except Exception as e:
        return {"repos": 0, "error": str(e)[:80]}

def validar_idea(idea: dict) -> dict:
    """
    Ejecuta validación real y devuelve:
    - score_mercado_real (0-100)
    - evidencias dict
    - ajuste_score (+-10 sobre score IA)
    """
    nombre   = idea.get("nombre", "")
    problema = idea.get("problema", "")[:100]
    tags     = idea.get("tags", [])
    tagline  = idea.get("tagline", "")

    print(f"🔍 Validando '{nombre}' con datos reales...")

    # 1. Google Trends
    keywords_trends = [nombre, tagline[:50]]
    trends = _google_trends(keywords_trends)
    time.sleep(1)

    # 2. Reddit (evidencia de que el problema existe)
    reddit = _reddit_evidencia(problema)
    time.sleep(0.5)

    # 3. GitHub (señal técnica de demanda)
    github = _github_demanda(nombre, tags)

    # ── Calcular score_mercado_real
    score = 50  # base

    # Trends
    trend_val = max(trends.values(), default=0) if isinstance(trends, dict) and "error" not in trends else 0
    if trend_val >= 50:
        score += 20
    elif trend_val >= 25:
        score += 10
    elif trend_val >= 10:
        score += 5

    # Reddit
    posts = reddit.get("posts", 0)
    votos = reddit.get("upvotes_total", 0)
    if posts >= 5 and votos >= 100:
        score += 20
    elif posts >= 3:
        score += 10
    elif posts >= 1:
        score += 5

    # GitHub
    repos = github.get("repos", 0)
    if 5 <= repos <= 30:
        score += 10   # Hay demanda pero poca competencia — sweet spot
    elif repos > 30:
        score += 5    # Competencia existente — señal positiva pero más dura
    elif repos == 0:
        score -= 5    # Nadie lo construyó — puede ser nicho o sin demanda

    score = max(0, min(100, score))

    # ── Ajuste sobre score IA
    score_ia = idea.get("scores", {}).get("score_total", 70) if isinstance(idea.get("scores"), dict) else 70
    ajuste   = round((score - 50) / 10, 1)  # +-5 puntos máximo
    score_ia_ajustado = round(min(100, max(0, score_ia + ajuste)), 1)

    evidencias = {
        "google_trends":       trends,
        "reddit":              reddit,
        "github":              github,
        "score_mercado_real":  score,
        "score_ia_original":   score_ia,
        "ajuste_aplicado":     ajuste,
        "score_final_ajustado": score_ia_ajustado,
    }

    print(f"   📊 Score mercado real: {score}/100 | Ajuste: {ajuste:+.1f} | Score final: {score_ia_ajustado}")
    if reddit.get("top_post"):
        print(f"   🔴 Reddit evidence: \"{reddit['top_post'][:80]}\"")

    return evidencias

# aqui finaliza el codigo de agents/market_validator.py