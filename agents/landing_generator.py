import os
import json
import base64
import requests
import re
from datetime import datetime

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO   = os.environ.get("GITHUB_PAGES_REPO", "")
GITHUB_BRANCH = "gh-pages"

def _slug(nombre: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")

def _generar_html(idea: dict) -> str:
    nombre   = idea.get("nombre", "SinNombre")
    tagline  = idea.get("tagline", "")
    problema = idea.get("problema", "")[:300]
    solucion = idea.get("solucion", "")[:300]
    scores   = idea.get("scores", {})
    score    = scores.get("score_total", 0) if isinstance(scores, dict) else 0
    tags     = idea.get("tags", []) if isinstance(idea.get("tags"), list) else []
    vertical = idea.get("vertical", "SaaS")
    fecha    = datetime.now().strftime("%d/%m/%Y")
    herr_ia  = idea.get("herramienta_ia_clave", "")

    tags_html = " ".join(f'<span class="tag">{t}</span>' for t in tags[:4])
    herr_html = (
        f'<p class="ia-tool">Construido con: <strong>{herr_ia[:100]}</strong></p>'
        if herr_ia else ""
    )

    if score >= 85:
        color_score = "#00c851"
        label_score = "IDEA PREMIUM"
    elif score >= 75:
        color_score = "#ffbb33"
        label_score = "ALTA PROBABILIDAD"
    else:
        color_score = "#ff4444"
        label_score = "EN VALIDACION"

    google_script_url = os.environ.get("GOOGLE_SCRIPT_URL", "")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{nombre} - {tagline}</title>
<meta name="description" content="{tagline}">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0a;color:#f0f0f0}}
.hero{{min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;
       text-align:center;padding:2rem;
       background:linear-gradient(135deg,#0a0a0a 0%,#1a1a2e 50%,#16213e 100%)}}
.badge{{display:inline-block;background:{color_score}22;border:1px solid {color_score};
        color:{color_score};padding:.4rem 1rem;border-radius:2rem;font-size:.85rem;
        font-weight:600;margin-bottom:1.5rem}}
h1{{font-size:clamp(2.5rem,8vw,5rem);font-weight:800;letter-spacing:-2px;
    background:linear-gradient(135deg,#fff 0%,#a8b8ff 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}}
.tagline{{font-size:clamp(1.1rem,3vw,1.6rem);color:#a0aec0;margin-bottom:2rem;max-width:600px}}
.tags{{margin-bottom:2rem}}
.tag{{background:#ffffff15;border:1px solid #ffffff25;padding:.3rem .8rem;
      border-radius:1rem;font-size:.8rem;color:#a0aec0;margin:.25rem;display:inline-block}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;max-width:800px;width:100%;margin:2rem auto}}
@media(max-width:600px){{.cards{{grid-template-columns:1fr}}}}
.card{{background:#ffffff08;border:1px solid #ffffff15;border-radius:1rem;padding:1.5rem;text-align:left}}
.card h3{{font-size:.8rem;text-transform:uppercase;letter-spacing:1px;color:#718096;margin-bottom:.75rem}}
.card p{{color:#e2e8f0;line-height:1.6;font-size:.95rem}}
.ia-tool{{color:#7c83ff;font-size:.85rem;margin:1rem 0}}
.form-group{{display:flex;gap:.5rem;margin-top:1.5rem;max-width:400px;width:100%}}
.form-group input{{flex:1;padding:.85rem 1rem;border-radius:.6rem;border:1px solid #ffffff25;
                   background:#ffffff10;color:#fff;font-size:1rem;outline:none}}
.form-group input::placeholder{{color:#718096}}
.form-group button{{padding:.85rem 1.5rem;background:#667eea;border:none;border-radius:.6rem;
                    color:#fff;font-weight:700;cursor:pointer;font-size:1rem;white-space:nowrap}}
.meta{{margin-top:3rem;color:#4a5568;font-size:.8rem}}
</style>
</head>
<body>
<section class="hero">
  <div class="badge">{label_score} - Score {score}/100</div>
  <h1>{nombre}</h1>
  <p class="tagline">{tagline}</p>
  <div class="tags">{tags_html}</div>
  {herr_html}
  <div class="cards">
    <div class="card">
      <h3>El Problema</h3>
      <p>{problema}</p>
    </div>
    <div class="card">
      <h3>La Solucion</h3>
      <p>{solucion}</p>
    </div>
  </div>
  <p style="color:#a0aec0;margin-top:1.5rem">Unete a la lista de espera:</p>
  <div class="form-group">
    <input type="email" id="email" placeholder="tu@email.com">
    <button onclick="joinWaitlist()">Quiero acceso</button>
  </div>
  <div class="meta">{vertical} · Generado {fecha} · ValidationIdea v4</div>
</section>
<script>
function joinWaitlist(){{
  var email=document.getElementById('email').value;
  if(!email||!email.includes('@')){{alert('Email invalido');return;}}
  var url='{google_script_url}';
  if(url){{
    fetch(url+'?email='+encodeURIComponent(email)+'&idea={nombre}')
      .then(function(){{alert('Apuntado! Te avisamos en el lanzamiento.');}})
      .catch(function(){{alert('Recibido!');}});
  }}else{{alert('Apuntado! Te avisamos en el lanzamiento.');}}
}}
</script>
</body>
</html>"""

def _subir_github_pages(slug: str, html: str) -> str:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return ""
    try:
        ruta    = f"ideas/{slug}/index.html"
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ruta}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept":        "application/vnd.github.v3+json"
        }
        sha = ""
        r = requests.get(api_url, headers=headers, timeout=8)
        if r.status_code == 200:
            sha = r.json().get("sha", "")
        payload = {
            "message": f"landing: {slug}",
            "content": base64.b64encode(html.encode("utf-8")).decode("utf-8"),
            "branch":  GITHUB_BRANCH,
        }
        if sha:
            payload["sha"] = sha
        r2 = requests.put(api_url, headers=headers, json=payload, timeout=15)
        if r2.status_code in (200, 201):
            usuario = GITHUB_REPO.split("/")[0]
            repo    = GITHUB_REPO.split("/")[1]
            url     = f"https://{usuario}.github.io/{repo}/ideas/{slug}/"
            print(f"  Landing GitHub Pages: {url}")
            return url
        else:
            print(f"  GitHub Pages HTTP {r2.status_code}: {r2.text[:150]}")
            return ""
    except Exception as e:
        print(f"  GitHub Pages error: {e}")
        return ""

def _guardar_local(slug: str, html: str) -> str:
    try:
        os.makedirs(f"data/landings/{slug}", exist_ok=True)
        ruta = f"data/landings/{slug}/index.html"
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Landing local: {ruta}")
        return ruta
    except Exception as e:
        print(f"  Error landing local: {e}")
        return ""

def generar_landing(idea: dict) -> dict:
    nombre = idea.get("nombre", "SinNombre")
    slug   = _slug(nombre)
    print(f"Landing: {nombre}")
    html        = _generar_html(idea)
    url_publica = _subir_github_pages(slug, html)
    ruta_local  = _guardar_local(slug, html)
    return {
        "slug":        slug,
        "url_publica": url_publica,
        "ruta_local":  ruta_local,
        "html_size":   len(html),
    }

# aqui finaliza el codigo de agents/landing_generator.py
