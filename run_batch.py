import os
import sys
import json
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

def ejecutar_batch():
    print(f"\n{'='*50}")
    print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from agents.generator_agent import generar_idea
    from agents.critic_agent import critique
    from agents.knowledge_base import aprender
    from agents.notion_sync_agent import sync_idea_to_notion
    from agents.cola_csv import guardar_en_cola

    # Cargar ideas existentes
    ideas_existentes = []
    ruta_ideas = os.path.join("data", "ideas.json")
    if os.path.exists(ruta_ideas):
        try:
            with open(ruta_ideas, "r", encoding="utf-8") as f:
                ideas_existentes = json.load(f)
        except:
            ideas_existentes = []

    # 1. Generar 1 idea
    print("🧠 Generando idea...")
    idea = generar_idea(ideas_existentes)
    if not idea:
        print("❌ No se pudo generar idea")
        return False

    nombre = idea.get("nombre", "Sin nombre")
    print(f"💡 Idea: {nombre}")

    # 2. Evaluar
    print("🔍 Evaluando...")
    try:
        evaluacion = critique(idea)
        if evaluacion:
            idea.update(evaluacion)
            score_general = (
                idea.get("score_critico", 0) * 0.4 +
                idea.get("score_generador", 0) * 0.3 +
                idea.get("viral_score", 0) * 0.2 +
                idea.get("score_money", 0) * 0.1
            )
            idea["score_general"] = round(score_general, 1)
            print(f"📊 Score: {idea['score_general']}/100 | C:{idea.get('score_critico')} V:{idea.get('viral_score')} G:{idea.get('score_generador')} M:{idea.get('score_money')}")
    except Exception as e:
        print(f"⚠️ Error evaluando: {e}")
        idea["score_general"] = 70.0

    # 3. Guardar local
    ideas_existentes.append(idea)
    os.makedirs("data", exist_ok=True)
    try:
        with open(ruta_ideas, "w", encoding="utf-8") as f:
            json.dump(ideas_existentes, f, ensure_ascii=False, indent=2)
        print("💾 Guardada")
    except Exception as e:
        print(f"⚠️ Error guardando: {e}")

    # 4. KB
    try:
        score_kb = idea.get("score_generador", 70)
        aprender(idea, score_kb)
    except Exception as e:
        print(f"⚠️ Error KB: {e}")

    # 5. Notion
    print("🔗 Sincronizando Notion...")
    try:
        resultado = sync_idea_to_notion(idea)
        if resultado:
            print(f"✅ Sincronizada: {nombre}")
            return True
        else:
            raise Exception("Notion devolvió None")
    except Exception as e:
        print(f"❌ Notion falló: {e}")
        try:
            guardar_en_cola(nombre_idea=nombre, motivo_fallo=str(e), datos_json=idea)
            print("📋 Guardada en cola CSV")
        except:
            pass
        return False

if __name__ == "__main__":
    exito = ejecutar_batch()
    sys.exit(0 if exito else 1)
# FIN COMPLETO run_batch.py
