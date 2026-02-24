import os
import re
import base64
import requests
from datetime import datetime

GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
GITHUB_PAGES_REPO = os.environ.get("GITHUB_PAGES_REPO", "")
GITHUB_BRANCH     = "main"


def _slug(nombre: str) -> str:
    s = nombre.lower()
    for src, dst in [("á","a"),("à","a"),("ä","a"),("é","e"),("è","e"),("ë","e"),
                     ("í","i"),("ì","i"),("ï","i"),("ó","o"),("ò","o"),("ö","o"),
                     ("ú","u"),("ù","u"),("ü","u"),("ñ","n")]:
        s = s.replace(src, dst)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:50]


def _generar_html(idea: dict) -> str:
    nombre   = idea.get("nombre",        "Idea")
    problema = idea.get("problema",      "")
    solucion = idea.get("solucion",      "")
    valor    = idea.get("propuesta_valor", problema[:200])
    target   = idea.get("vertical",      idea.get("cliente_objetivo", ""))
    negocio  = idea.get("modelo_negocio", idea.get("monetizacion", ""))
    score    = idea.get("score_generador", idea.get("ScoreGen", "—"))
    mes      = datetime.now().strftime("%B %Y")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{nombre}</title>
  <meta name="description" content="{str(valor)[:160]}">
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}}
    .hero{{background:linear-gradient(135deg,#1e293b,#0f172a);padding:80px 24px 60px;text-align:center;border-bottom:1px solid #1e293b}}
    .badge{{display:inline-block;background:#22c55e22;color:#22c55e;border:1px solid #22c55e44;padding:6px 16px;border-radius:999px;font-size:13px;font-weight:700;margin-bottom:24px}}
    h1{{font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:#f8fafc;margin-bottom:16px;line-height:1.1}}
    .sub{{font-size:1.15rem;color:#94a3b8;max-width:600px;margin:0 auto 40px;line-height:1.6}}
    .form{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;max-width:500px;margin:0 auto}}
    .form input{{flex:1;min-width:240px;padding:14px 20px;border-radius:10px;border:1px solid #334155;background:#1e293b;color:#f8fafc;font-size:1rem;outline:none}}
    .form input:focus{{border-color:#6366f1}}
    .form button{{padding:14px 28px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:700;cursor:pointer;transition:.2s}}
    .form button:hover{{background:#4f46e5}}
    .hint{{font-size:12px;color:#475569;margin-top:12px}}
    .scores{{display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin:50px auto;max-width:560px;padding:0 24px}}
    .sb{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px 28px;text-align:center;flex:1;min-width:120px}}
    .sn{{font-size:2rem;font-weight:800;color:#6366f1}}
    .sl{{font-size:12px;color:#64748b;margin-top:4px}}
    .section{{max-width:800px;margin:0 auto 60px;padding:0 24px}}
    .card{{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:32px;margin-bottom:20px}}
    .lbl{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#6366f1;margin-bottom:10px}}
    .txt{{font-size:1.05rem;line-height:1.7;color:#cbd5e1}}
    footer{{text-align:center;padding:40px 24px;color:#475569;font-size:13px;border-top:1px solid #1e293b}}
    footer a{{color:#6366f1;text-decoration:none}}
  </style>
</head>
<body>
  <div class="hero">
    <div class="badge">💡 Score {score}/100 — Idea validada automáticamente</div>
    <h1>{nombre}</h1>
    <p class="sub">{valor}</p>
    <form class="form" onsubmit="return reg(event)">
      <input type="email" id="em" placeholder="tu@email.com" required>
      <button type="submit">Me interesa →</button>
    </form>
    <p class="hint">Sin spam. Solo te avisamos si el proyecto avanza.</p>
  </div>

  <div class="scores">
    <div class="sb"><div class="sn">{score}</div><div class="sl">Viabilidad</div></div>
    <div class="sb"><div class="sn">🎯</div><div class="sl">Mercado real</div></div>
    <div class="sb"><div class="sn">🚀</div><div class="sl">MVP 30 días</div></div>
  </div>

  <div class="section">
    <div class="card"><div class="lbl">El problema</div><div class="txt">{problema}</div></div>
    <div class="card"><div class="lbl">La solución</div><div class="txt">{solucion}</div></div>
    <div class="card"><div class="lbl">Modelo de negocio</div><div class="txt">{negocio}</div></div>
    <div class="card"><div class="lbl">Cliente ideal</div><div class="txt">{target}</div></div>
  </div>

  <footer>
    Generado por <a href="https://github.com/mipromptingeniering-alt/validationidea">ValidationIdea</a> · {mes}
  </footer>

  <script>
    function reg(e){{
      e.preventDefault();
      const b=e.target.querySelector('button');
      b.textContent='✅ ¡Apuntado!';
      b.style.background='#22c55e';
      b.disabled=true;
      return false;
    }}
  </script>
</body>
</html>"""


def _github_upsert(repo: str, path: str, contenido: str, token: str, msg: str) -> bool:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    sha = None
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        sha = r.json().get("sha")

    body = {
        "message": msg,
        "content": base64.b64encode(contenido.encode("utf-8")).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        body["sha"] = sha

    r = requests.put(url, headers=headers, json=body, timeout=15)
    return r.status_code in (200, 201)


def publicar_landing(idea: dict) -> str | None:
    """Genera HTML y lo sube a GitHub Pages. Retorna URL pública o None."""
    if not GITHUB_TOKEN or not GITHUB_PAGES_REPO:
        print("[Landing] ⚠️ GITHUB_TOKEN o GITHUB_PAGES_REPO no configurados — saltando")
        return None

    try:
        nombre = idea.get("nombre", "idea")
        slug   = _slug(nombre)
        html   = _generar_html(idea)
        path   = f"ideas/{slug}.html"

        ok = _github_upsert(
            repo=GITHUB_PAGES_REPO,
            path=path,
            contenido=html,
            token=GITHUB_TOKEN,
            msg=f"feat: landing automática para '{nombre}'"
        )

        if not ok:
            print(f"[Landing] ❌ Error al subir a GitHub")
            return None

        usuario = GITHUB_PAGES_REPO.split("/")[0]
        repo_n  = GITHUB_PAGES_REPO.split("/")[1]
        if repo_n == f"{usuario}.github.io":
            url = f"https://{usuario}.github.io/ideas/{slug}.html"
        else:
            url = f"https://{usuario}.github.io/{repo_n}/ideas/{slug}.html"

        print(f"[Landing] ✅ Publicada: {url}")
        return url

    except Exception as e:
        print(f"[Landing] ❌ Error: {e}")
        return None
