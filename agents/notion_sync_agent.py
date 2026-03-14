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
    ee_txt = "Conservador: "+str(_c12)+"EUR/mes12 | Breakeven: "+str(_cb)+"\nRealista: "+str(_r12)+"EUR/mes12 | Breakeven: "+str(_rb)+"\nOptimista: "+str(_o12)+"EUR/mes12 | Breakeven: "+str(_ob)
    op_txt = ("Unicidad: "+_s(op.get("unicidad",""),200)+"\n"+
             "Riesgo: "+_s(op.get("riesgo_principal",""),150)+"\n"+
             "Timing: "+_s(op.get("timing",""),150)+"\n"+
             "Dia uno: "+_s(op.get("dia_uno",""),150)+"\n"+
             "Fallo probable: "+_s(op.get("fallo_probable",""),150))
    hr_txt = ("S1: "+_s(hr.get("semana1",""),150)+"\n"+
             "S2: "+_s(hr.get("semana2",""),150)+"\n"+
             "S3: "+_s(hr.get("semana3",""),150)+"\n"+
             "S4: "+_s(hr.get("semana4",""),150))
    canales_txt = "\n".join("- "+_s(c,150) for c in mn.get("canales_adquisicion",[])[:5])
    comp_txt    = "\n".join("- "+_s(c,150) for c in merc.get("competidores",[])[:5])

    primer_cli  = _s(pm.get("primer_cliente_script",""), 400)

    properties = {
        "Name":  {"title": _rt(f"{emoji} {nombre} — {score}/100")},
            }

    # Propiedades adicionales
    properties["Score"]         = {"number": float(score)}
    properties["Ejecutabilidad"]= {"number": float(ejec)}
    properties["MRR_M12"]       = {"number": float(_c12) if _c12 else 0}
    properties["Tagline"]       = {"rich_text": _rt(tagline)}
    properties["Veredicto"]     = {"rich_text": _rt(_s(str(veredicto), 300))}
    properties["Stack"]         = {"rich_text": _rt(_s(mvp.get("stack_recomendado",""), 200))}
    properties["Fecha"]         = {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
    properties["Tags"]          = {"multi_select": [{"name": str(t)[:50]} for t in idea.get("tags",[])[:5]]}
    if vertical:     properties["Vertical"]      = {"select": {"name": vertical[:100]}}
    if tipo:         properties["Tipo"]          = {"select": {"name": tipo[:50]}}
    if recomendacion: properties["Recomendacion"] = {"select": {"name": recomendacion[:50]}}

    children = []
    children += _bloque("Resumen ejecutivo", tagline+"\n\n"+propuesta)
    children += _bloque("Problema", problema, 3)
    children += _bloque("Solucion", solucion, 3)
    children += _bloque("Cliente objetivo", cliente, 3)
    children += _bloque("Scoring detallado", "Score global: "+str(score)+"/100 | Critico YC: "+str(critico_s)+"/100\nEjecutabilidad: "+str(ejec)+" | Monetizacion: "+str(monetiz)+" | Viral: "+str(viral)+" | Timing: "+str(timing_s))
    children += _bloque("Veredicto YC", str(veredicto)+"\nRecomendacion: "+recomendacion.upper()+"\nObjeciones clave: "+_s(sc.get("objeciones_principales",[]),300)+"\nPivote sugerido: "+_s(sc.get("pivote_sugerido",""),200))
    children += _bloque("Opinion profesional", op_txt)
    children += _bloque("Estudio economico 3 escenarios", ee_txt)
    _mrr_r = ee_real.get("mes12",{}).get("mrr_eur",0) if isinstance(ee_real.get("mes12"),dict) else 0
    _ur = ee_real.get("mes3",{}).get("usuarios",10) if isinstance(ee_real.get("mes3"),dict) else 10
    _ltv = round(float(_mrr_r)/max(float(_ur),1)*24,0)
    _cac_max = round(_ltv/3,0)
    _ue = ("MRR mes12 realista: "+str(_mrr_r)+"EUR | MRR mes12 optimista: "+str(_o12)+"EUR\n"
           "Usuarios mes3 estimados: "+str(_ur)+"\n"
           "LTV estimado 24 meses: "+str(_ltv)+"EUR\n"
           "CAC maximo recomendado: "+str(_cac_max)+"EUR\n"
           "Payback period objetivo: 3 meses | Churn objetivo: menos 5pct/mes\n"
           "Margen bruto SaaS objetivo: 70-80pct | Break-even: "+str(_rb))
    children += _bloque("Unit Economics CAC/LTV/Churn", _ue)
    children += _bloque("Mercado TAM/SAM/SOM", "TAM: "+_s(merc.get("TAM",""),100)+" | SAM: "+_s(merc.get("SAM",""),100)+" | SOM: "+_s(merc.get("SOM",""),100)+"\nVentaja competitiva: "+_s(merc.get("ventaja_competitiva",""),300))
    if comp_txt: children += _bloque("Competidores y debilidades explotables", comp_txt, 3)
    children += _bloque("DAFO estrategico", "FORTALEZAS: "+_s(dafo.get("fortalezas",[]),200)+"\nDEBILIDADES: "+_s(dafo.get("debilidades",[]),200)+"\nOPORTUNIDADES: "+_s(dafo.get("oportunidades",[]),200)+"\nAMENAZAS: "+_s(dafo.get("amenazas",[]),200))
    children += _bloque("Estrategia monetizacion semana a semana", "SEMANA 1: "+_s(em.get("semana1",""),300)+"\nSEMANA 4: "+_s(em.get("semana4",""),200)+"\nMES 3: "+_s(em.get("mes3",""),200)+"\nPRECIO OPTIMO: "+_s(em.get("precio_optimo_justificado",""),200))
    if canales_txt: children += _bloque("Canales adquisicion prioritarios", canales_txt, 3)
    children += _bloque("Hipotesis 48h testeable", "EXPERIMENTO: "+_s(ht.get("experimento_48h",""),200)+"\nMETRICA EXITO: "+_s(ht.get("metrica_exito",""),150)+"\nSENAL DE ALARMA pivot: "+_s(ht.get("senal_de_alarma",""),150))
    _qw = ("DIA 0: Crea landing en Carrd.co gratis en 15min - describe el problema + formulario email\n"
           "DIA 1: "+_s(em.get("semana1","Envia 10 DMs personalizados a tu ICP"),200)+"\n"
           "DIA 2: Post en comunidad del sector preguntando por el problema - sin mencionar solucion\n"
           "DIA 3: Analiza respuestas, ajusta propuesta de valor, prepara demo de 5 slides\n"
           "DIA 5: Primera llamada discovery 30min con interesado - escucha, no vendas\n"
           "DIA 7: Envia propuesta con precio y solicita prepago o carta de intencion")
    children += _bloque("Quick Wins Semana 1 sin escribir codigo", _qw)
    _mvp_txt = ("STACK: "+_s(mvp.get("stack_recomendado","Next.js 14+Supabase+Vercel+Stripe"),200)+"\n"
               "TIEMPO: "+str(mvp.get("tiempo_semanas",3))+" semanas | COSTE: 0EUR\n"
               "FEATURES MINIMAS: "+_s(mvp.get("features_minimas",[]),400)+"\n\n"
               "HERRAMIENTAS 0EUR:\n"
               "- Vercel: hosting + deploy automatico desde GitHub\n"
               "- Supabase: PostgreSQL + Auth + Storage gratis\n"
               "- Stripe: pagos sin coste hasta cobrar\n"
               "- Resend: 100 emails/dia gratis\n"
               "- Clerk: auth alternativa 10k MAU gratis")
    children += _bloque("MVP Como construirlo GRATIS", _mvp_txt)
    _pm = mvp.get("prompt_mvp",{}) if isinstance(mvp.get("prompt_mvp"),dict) else {}
    _pm_meta = _pm.get("meta",{}) if isinstance(_pm,dict) else {}
    _ia = _pm_meta.get("ia_recomendada","Claude 3.5 Sonnet") if isinstance(_pm_meta,dict) else "Claude 3.5 Sonnet"
    _sys_def = "Eres dev senior experto en SaaS. Construye "+str(nombre)+" que resuelve: "+_s(str(problema),200)+". Stack: Next.js+Supabase+Vercel. Objetivo: MVP funcional en 3 semanas con 0EUR."
    _sys = _pm.get("system_prompt",_sys_def) if isinstance(_pm,dict) else _sys_def
    _steps = _pm.get("instrucciones_paso_a_paso",["1. npx create-next-app@latest --typescript --tailwind","2. supabase init + crear tablas","3. Implementar feature principal con IA","4. Stripe checkout + webhook","5. Deploy en Vercel + dominio"]) if isinstance(_pm,dict) else []
    _pt = ("IA RECOMENDADA: "+str(_ia)+"\n"
           "ALTERNATIVAS GRATUITAS: Groq Llama3.3-70B | Gemini 1.5 Flash | Mistral 7B | HuggingFace Inference API\n\n"
           "=== COPIA ESTE PROMPT EN CLAUDE O CURSOR ===\n"
           +str(_sys)[:600]+"\n\n"
           "=== PASOS EXACTOS DE IMPLEMENTACION ===\n"
           +_s(_steps,700))
    children += _bloque("Prompt completo para construir el MVP con IA", _pt)
    children += _bloque("Hoja de ruta semana a semana", hr_txt)
    children += _bloque("Herramienta IA principal y alternativas gratuitas", herr_ia+"\n\nALTERNATIVAS 0EUR:\n- Groq API: Llama3.3-70B ultrarapido\n- Google Gemini Flash: 1M tokens/dia gratis\n- Mistral API: 7B y Mixtral gratis\n- HuggingFace: inference gratuita")
    if primer_cli: children += _bloque("Script primer cliente - copia y pega exacto", primer_cli)


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