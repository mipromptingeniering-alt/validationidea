import os
import sys
import json
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

SCORE_LANDING_MINIMO = 85   # P9: umbral para generar landing automática


def ejecutar_batch():
    print(f"\n{'=' * 50}")
    print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from agents.generator_agent import generar_idea
    from agents.critic_agent    import critique
    from agents.knowledge_base  import aprender
    from agents.notion_sync_agent import sync_idea_to_notion
    from agents.cola_csv        import guardar_en_cola

    # Cargar ideas existentes para evitar repeticiones
    ideas_existentes = []
    ruta_ideas = os.path.join("data", "ideas.json")
    if os.path.exists(ruta_ideas):
        try:
            with open(ruta_ideas, "r", encoding="utf-8") as f:
                ideas_existentes = json.load(f)
        except Exception:
            ideas_existentes = []

    # 1. Generar idea (P1 KB context + P10 detector semántico)
    print("🧠 Generando idea con KB context + detector semántico...")
    idea = generar_idea(ideas_existentes)
    if not idea:
        print("❌ No se pudo generar la idea")
        return False

    nombre = idea.get("nombre", "Idea sin nombre")
    print(f"💡 Idea: {nombre}")

    # 2. Evaluar con critique() (P5 ScoreMoney incluido)
    print("🔍 Evaluando con critic_agent...")
    try:
        evaluacion = critique(idea)
        if evaluacion:
            idea.update(evaluacion)
            sc = idea.get("score_critico")
            sv = idea.get("viral_score")
            sg = idea.get("score_generador")
            sm = idea.get("score_money")
            print(f"📊 Critico:{sc} | Viral:{sv} | Gen:{sg} | Money:{sm}")
    except Exception as e:
        print(f"⚠️ Error evaluando (continuamos): {e}")

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
        score_kb = idea.get("score_generador")
        if score_kb is not None:
            aprender(idea, score_kb)
            print(f"📚 KB actualizada (score={score_kb})")
    except Exception as e:
        print(f"⚠️ Error actualizando KB: {e}")

    # 5. Sincronizar con Notion — P2: cola CSV si falla
    print("🔗 Sincronizando con Notion...")
    notion_page = None
    try:
        notion_page = sync_idea_to_notion(idea)
        if notion_page:
            print(f"✅ Sincronizada en Notion: {nombre}")
        else:
            raise Exception("sync_idea_to_notion devolvió None/False")
    except Exception as e:
        print(f"❌ Fallo Notion: {e}")
        guardar_en_cola(
            nombre_idea=nombre,
            motivo_fallo=str(e),
            datos_json=idea
        )
        print("📋 Idea en cola CSV — se reintentará en 5 min")
        return False

    # 6. P9: Landing automática si score_generador >= 85
    score_para_landing = idea.get("score_generador")
    if score_para_landing is not None and score_para_landing >= SCORE_LANDING_MINIMO:
        print(f"🌐 Score {score_para_landing} >= {SCORE_LANDING_MINIMO} — generando landing...")
        try:
            from agents.landing_agent import publicar_landing
            url_landing = publicar_landing(idea)
            if url_landing:
                print(f"🌐 Landing publicada: {url_landing}")
                # Actualizar Notion con URL de landing
                if notion_page:
                    try:
                        import requests as req
                        token   = os.environ.get("NOTION_TOKEN", "")
                        page_id = notion_page.get("id", "")
                        if page_id and token:
                            req.patch(
                                f"https://api.notion.com/v1/pages/{page_id}",
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "Notion-Version": "2022-06-28",
                                    "Content-Type": "application/json"
                                },
                                json={"properties": {
                                    "Research": {"rich_text": [{"text": {"content": f"Landing: {url_landing}"}}]}
                                }},
                                timeout=15
                            )
                    except Exception:
                        pass
        except Exception as e:
            print(f"⚠️ Error generando landing (no crítico): {e}")

    return True


if __name__ == "__main__":
    exito = ejecutar_batch()
    sys.exit(0 if exito else 1)
