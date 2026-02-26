@"
import os
import sys
import json
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

SCORE_LANDING_MINIMO = 85


def ejecutar_batch():
    print(f"\n{'=' * 50}")
    print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from agents.generator_agent import generar_idea
    from agents.critic_agent import critique
    from agents.knowledge_base import aprender
    from agents.notion_sync_agent import sync_idea_to_notion
    from agents.cola_csv import guardar_en_cola

    ideas_existentes = []
    ruta_ideas = os.path.join("data", "ideas.json")
    if os.path.exists(ruta_ideas):
        try:
            with open(ruta_ideas, "r", encoding="utf-8") as f:
                ideas_existentes = json.load(f)
        except Exception:
            ideas_existentes = []

    print("🧠 Generando idea con contexto KB...")
    idea = generar_idea(ideas_existentes)
    if not idea:
        print("❌ No se pudo generar la idea")
        return False

    nombre = idea.get("nombre", "Idea sin nombre")
    print(f"💡 Idea: {nombre}")

    print("🔍 Evaluando con critic_agent...")
    try:
        evaluacion = critique(idea)
        if evaluacion:
            idea.update(evaluacion)
            sc = idea.get("score_critico",   0)
            sv = idea.get("viral_score",     0)
            sg = idea.get("score_generador", 0)
            sm = idea.get("score_money",     0)
            print(f"📊 Critico:{sc} | Viral:{sv} | Gen:{sg} | Money:{sm}")
    except Exception as e:
        print(f"⚠️ Error evaluando (continuamos): {e}")

    ideas_existentes.append(idea)
    os.makedirs("data", exist_ok=True)
    try:
        with open(ruta_ideas, "w", encoding="utf-8") as f:
            json.dump(ideas_existentes, f, ensure_ascii=False, indent=2)
        print("💾 Guardada en data/ideas.json")
    except Exception as e:
        print(f"⚠️ Error guardando local: {e}")

    try:
        score_kb = idea.get("score_generador")
        if score_kb is not None:
            aprender(idea, score_kb)
            print(f"📚 KB actualizada (score={score_kb})")
    except Exception as e:
        print(f"⚠️ Error actualizando KB: {e}")

    print("🔗 Sincronizando con Notion...")
    try:
        resultado = sync_idea_to_notion(idea)
        if resultado:
            print(f"✅ Sincronizada en Notion: {nombre}")
        else:
            raise Exception("sync_idea_to_notion devolvio None/False")
    except Exception as e:
        print(f"❌ Fallo Notion: {e}")
        guardar_en_cola(nombre_idea=nombre, motivo_fallo=str(e), datos_json=idea)
        print("📋 Idea en cola CSV")
        return False

    score_para_landing = idea.get("score_generador", 0) or 0
    if score_para_landing >= SCORE_LANDING_MINIMO:
        print(f"🌐 Score {score_para_landing} >= {SCORE_LANDING_MINIMO} — generando landing...")
        try:
            from agents.landing_agent import publicar_landing
            url = publicar_landing(idea)
            if url:
                print(f"🌐 Landing: {url}")
        except Exception as e:
            print(f"⚠️ Error landing (no critico): {e}")

    return True


if __name__ == "__main__":
    exito = ejecutar_batch()
    sys.exit(0 if exito else 1)
"@ | Set-Content run_batch.py -Encoding UTF8

# Quitar BOM
$c = Get-Content run_batch.py -Raw
$c = $c.TrimStart([char]0xFEFF)
[System.IO.File]::WriteAllText((Resolve-Path run_batch.py), $c, [System.Text.UTF8Encoding]::new($false))

python -c "import ast; ast.parse(open('run_batch.py', encoding='utf-8').read()); print('Sintaxis OK')"
