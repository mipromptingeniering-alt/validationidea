import os, json, urllib.request, urllib.error
from datetime import datetime

NOTION_TOKEN   = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID   = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_API     = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

def _headers():
    return {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": NOTION_VERSION}

def _post(endpoint, payload, timeout=20):
    url  = f"{NOTION_API}{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion HTTP {e.code}: {body[:300]}")
    except Exception as e:
        raise RuntimeError(f"Notion: {e}")

def _t(v, n=2000): return str(v)[:n] if v else ""
def _rt(v, n=2000): return [{"type":"text","text":{"content":_t(v,n)}}]
def _s(v, n=200):
    if isinstance(v,list): return _t(", ".join(str(x) for x in v), n)
    if isinstance(v,dict): return _t(json.dumps(v,ensure_ascii=False), n)
    return _t(str(v) if v else "", n)

def _bloque(titulo, contenido, nivel=2):
    tipo = f"heading_{nivel}"
    return [
        {"object":"block","type":tipo,tipo:{"rich_text":_rt(titulo)}},
        {"object":"block","type":"paragraph","paragraph":{"rich_text":_rt(contenido)}},
    ]

def sync_idea_to_notion(idea):
    if not NOTION_TOKEN or not NOTION_DB_ID or not isinstance(idea, dict):
        return ""

    nombre    = _s(idea.get("nombre","SinNombre"), 100)
    tagline   = _s(idea.get("tagline",""), 200)
    problema  = _s(idea.get("problema",""), 500)
    solucion  = _s(idea.get("solucion",""), 500)
    cliente   = _s(idea.get("cliente_objetivo",""), 300)
    vertical  = _s(idea.get("vertical","SaaS"), 100)
    tipo      = _s(idea.get("tipo","B2B"), 50)
    herr_ia   = _s(idea.get("herramienta_ia_clave",""), 300)
    propuesta = _s(idea.get("propuesta_valor_unica",""), 300)

    scores    = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
    score     = scores.get("score_total",0)
    ejec      = scores.get("ejecutabilidad",0)
    viral     = scores.get("viral",0)
    timing_s  = scores.get("timing",0)
    monetiz   = scores.get("monetizacion",0)
    critico_s = scores.get("score_critico",0)

    em   = idea.get("estrategia_monetizacion",{}) if isinstance(idea.get("estrategia_monetizacion"),dict) else {}
    ht   = idea.get("hipotesis_testeable",{}) if isinstance(idea.get("hipotesis_testeable"),dict) else {}
    sc   = idea.get("scoring_critico",{}) if isinstance(idea.get("scoring_critico"),dict) else {}
    mvp  = idea.get("mvp",{}) if isinstance(idea.get("mvp"),dict) else {}
    dafo = idea.get("dafo",{}) if isinstance(idea.get("dafo"),dict) else {}
    merc = idea.get("mercado",{}) if isinstance(idea.get("mercado"),dict) else {}
    mn   = idea.get("modelo_negocio",{}) if isinstance(idea.get("modelo_negocio"),dict) else {}
    op   = idea.get("opinion_profesional",{}) if isinstance(idea.get("opinion_profesional"),dict) else {}
    hr   = idea.get("hoja_de_ruta",{}) if isinstance(idea.get("hoja_de_ruta"),dict) else {}
    pm   = idea.get("prompt_mvp",{}) if isinstance(idea.get("prompt_mvp"),dict) else {}
    ee   = idea.get("estudio_economico",{}) if isinstance(idea.get("estudio_economico"),dict) else {}

    recomendacion = _s(sc.get("recomendacion","pivotar"), 50) or "pivotar"
    veredicto     = _s(sc.get("veredicto",""), 300)

    if   score >= 90: emoji = "💎"
    elif score >= 85: emoji = "⭐"
    elif score >= 80: emoji = "🔥"
    elif score >= 75: emoji = "✅"
    else:             emoji = "💡"

    ee_cons = ee.get("conservador",{}) if isinstance(ee.get("conservador"),dict) else {}
    ee_real = ee.get("realista",{}) if isinstance(ee.get("realista"),dict) else {}
    ee_opt  = ee.get("optimista",{}) if isinstance(ee.get("optimista"),dict) else {}
    _c12 = ee_cons.get("mes12", {}).get("mrr_eur", 0) if isinstance(ee_cons.get("mes12"), dict) else 0
    _r12 = ee_real.get("mes12", {}).get("mrr_eur", 0) if isinstance(ee_real.get("mes12"), dict) else 0
    _o12 = ee_opt.get("mes12",  {}).get("mrr_eur", 0) if isinstance(ee_opt.get("mes12"),  dict) else 0
    _cb  = ee_cons.get("breakeven", "?")
    _rb  = ee_real.get("breakeven", "?")
    _ob  = ee_opt.get("breakeven",  "?")
    ee_txt = f"Conservador: {_c12}EUR/mes12 | Breakeven: {_cb}\nRealista: {_r12}EUR/mes12 | Breakeven: {_rb}\nOptimista: {_o12}EUR/mes12 | Breakeven: {_ob}"
"
               f"Realista:    {ee_real.get('mes12',{}).get('mrr_eur',0) if isinstance(ee_real.get('mes12'),dict) else 0}EUR/mes12 | Breakeven: {ee_real.get('breakeven','?')}
"
               f"Optimista:   {ee_opt.get('mes12',{}).get('mrr_eur',0) if isinstance(ee_opt.get('mes12'),dict) else 0}EUR/mes12 | Breakeven: {ee_opt.get('breakeven','?')}")

    op_txt = (f"Unicidad: {_s(op.get('unicidad',''),200)}
Riesgo: {_s(op.get('riesgo_principal',''),150)}
"
              f"Timing: {_s(op.get('timing',''),150)}
Dia uno: {_s(op.get('dia_uno',''),150)}
Fallo probable: {_s(op.get('fallo_probable',''),150)}")

    hr_txt = (f"S1: {_s(hr.get('semana1',''),150)}
S2: {_s(hr.get('semana2',''),150)}
"
              f"S3: {_s(hr.get('semana3',''),150)}
S4: {_s(hr.get('semana4',''),150)}")

    canales_txt = "
".join(f"- {_s(c,150)}" for c in mn.get("canales_adquisicion",[])[:5])
    comp_txt    = "
".join(f"- {_s(c,150)}" for c in merc.get("competidores",[])[:5])
    primer_cli  = _s(pm.get("primer_cliente_script",""), 400)

    properties = {
        "Name":  {"title": _rt(f"{emoji} {nombre} — {score}/100")},
        "Score": {"number": float(score)},
        "Tagline": {"rich_text": _rt(tagline)},
        "Fecha": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        "Ejecutabilidad": {"number": float(ejec)},
        "Stack": {"rich_text": _rt(_s(mvp.get("stack_recomendado",""),200))},
        "Tags":  {"rich_text": _rt(", ".join(str(t) for t in idea.get("tags",[])[:5]))},
    }

    # Selects opcionales — solo si tienen valor
    if vertical: properties["Vertical"]      = {"select": {"name": vertical[:100]}}
    if tipo:     properties["Tipo"]          = {"select": {"name": tipo[:50]}}
    if recomendacion: properties["Recomendacion"] = {"select": {"name": recomendacion[:50]}}

    children = []
    children += _bloque("🚀 Resumen ejecutivo", f"{tagline}

{propuesta}")
    children += _bloque("❗ Problema", problema, 3)
    children += _bloque("💡 Solución", solucion, 3)
    children += _bloque("👤 Cliente objetivo", cliente, 3)
    children += _bloque("📊 Scoring", f"Total: {score}/100 | Crítico YC: {critico_s}/100
Ejecutabilidad: {ejec} | Monetización: {monetiz} | Viral: {viral} | Timing: {timing_s}")
    children += _bloque("✅ Veredicto YC", f"{veredicto}
Recomendacion: {recomendacion.upper()}
Objeciones: {_s(sc.get('objeciones_principales',[]),300)}")
    children += _bloque("🧠 Opinión profesional", op_txt)
    children += _bloque("📈 Estudio económico", ee_txt)
    children += _bloque("🌍 Mercado", f"TAM: {_s(merc.get('TAM',''),100)} | SAM: {_s(merc.get('SAM',''),100)} | SOM: {_s(merc.get('SOM',''),100)}
Ventaja: {_s(merc.get('ventaja_competitiva',''),300)}")
    if comp_txt: children += _bloque("⚔️ Competidores", comp_txt, 3)
    children += _bloque("🔲 DAFO", f"Fortalezas: {_s(dafo.get('fortalezas',[]),200)}
Debilidades: {_s(dafo.get('debilidades',[]),200)}
Oportunidades: {_s(dafo.get('oportunidades',[]),200)}
Amenazas: {_s(dafo.get('amenazas',[]),200)}")
    children += _bloque("💰 Monetización", f"S1: {_s(em.get('semana1',''),300)}
S4: {_s(em.get('semana4',''),200)}
Mes3: {_s(em.get('mes3',''),200)}
Precio: {_s(em.get('precio_optimo_justificado',''),200)}")
    if canales_txt: children += _bloque("📣 Canales", canales_txt, 3)
    children += _bloque("🧪 Hipótesis", f"Test: {_s(ht.get('experimento_48h',''),200)}
Métrica: {_s(ht.get('metrica_exito',''),150)}
Alarma: {_s(ht.get('senal_de_alarma',''),150)}")
    children += _bloque("🛠️ MVP", f"Stack: {_s(mvp.get('stack_recomendado',''),200)}
Tiempo: {mvp.get('tiempo_semanas',3)} semanas | Coste: 0€
Features: {_s(mvp.get('features_minimas',[]),300)}")
    children += _bloque("🗓️ Hoja de ruta", hr_txt)
    children += _bloque("🤖 Herramienta IA", herr_ia, 3)
    if primer_cli: children += _bloque("🎯 Primer cliente", primer_cli)

    payload = {"parent": {"database_id": NOTION_DB_ID}, "properties": properties, "children": children[:95]}

    try:
        result   = _post("/pages", payload)
        page_url = result.get("url","")
        page_id  = result.get("id","").replace("-","")
        if not page_url and page_id:
            page_url = f"https://notion.so/{page_id}"
        print(f"Notion OK: {page_url}")
        return page_url
    except Exception as e:
        print(f"Notion sync: {e}")
        return ""