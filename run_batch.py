import os
import sys
import json
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"


def ejecutar_batch():
    print(f"\n{'=' * 50}")
    print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from agents.generator_agent import generar_idea
    from agents.critic_agent import critique          # ← nombre real
    from agents.knowledge_base import aprender
    from agents.notion_sync_agent import sync_idea_to_notion
    from agents.cola_csv import guardar_en_cola

    # Cargar ideas existentes para evitar repeticiones
    ideas_existentes = []
    ruta_ideas = os.path.join("data", "ideas.json")
    if os.path.exists(ruta_ideas):
        try:
            with open(ruta_ideas, "r", encoding="utf-8") as f:
                ideas_existentes = json.load(f)
        except Exception:
            ideas_existentes = []

    # 1. Generar idea (con contexto KB — P1 activo)
    print("🧠 Generando idea con contexto KB...")
    idea = generar_idea(ideas_existentes)
    if not idea:
        print("❌ No se pudo generar la idea")
        return False

    nombre = idea.get("nombre", "Idea sin nombre")
    print(f"💡 Idea: {nombre}")

    # 2. Evaluar con critique()
    print("🔍 Evaluando con critic_agent...")
    try:
        evaluacion = critique(idea)
        if evaluacion:
            idea.update(evaluacion)
            score = idea.get("score_general")
            if score is None:
                score = idea.get("ScoreGen")
            print(f"📊 Score: {score}/100")
    except Exception as e:
        print(f"⚠️ Error evaluando (continuamos sin score): {e}")

    # 3. Guardar localmente
    ideas_existentes.append(idea)
    os.makedirs("data", exist_ok=True)
    try:
        with open(ruta_ideas, "w", encoding="utf-8") as f:
            json.dump(ideas_existentes, f, ensure_ascii=False, indent=2)
        print("💾 Guardada en data/ideas.json")
    except Exception as e:
        print(f"⚠️ Error guardando local: {e}")

    # 4. Actualizar Knowledge Base
    try:
        score_kb = idea.get("score_generador")      # ← nombre real de critique()
        if score_kb is not None:
            aprender(idea, score_kb)
            print(f"📚 KB actualizada (score={score_kb})")
        else:
            print("⚠️ score_generador no encontrado, KB no actualizada")
    except Exception as e:
        print(f"⚠️ Error actualizando KB: {e}")

    # 5. Sincronizar con Notion — P2: cola CSV si falla
    print("🔗 Sincronizando con Notion...")
    try:
        resultado = sync_idea_to_notion(idea)
        if resultado:
            print(f"✅ Sincronizada en Notion: {nombre}")
            return True
        else:
            raise Exception("sync_idea_to_notion devolvió None/False")
    except Exception as e:
        print(f"❌ Fallo Notion: {e}")
        guardar_en_cola(
            nombre_idea=nombre,
            motivo_fallo=str(e),
            datos_json=idea
        )
        print("📋 Idea en cola CSV — se reintentará automáticamente cada 5 min")
        return False


if __name__ == "__main__":
    exito = ejecutar_batch()
    sys.exit(0 if exito else 1)
