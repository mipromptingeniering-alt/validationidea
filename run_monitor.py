import os, sys, json, csv
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("📄 run_monitor.py — procesando cola y pendientes...")

def procesar_cola():
    ruta = "data/cola_pendientes.csv"
    if not os.path.exists(ruta):
        print("✅ Sin cola pendiente")
        return

    try:
        from agents.notion_sync_agent import sync_idea_to_notion
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return

    with open(ruta, newline="", encoding="utf-8") as f:
        pendientes = list(csv.DictReader(f))

    if not pendientes:
        print("✅ Cola vacía")
        return

    print(f"📋 Cola CSV: {len(pendientes)} pendiente(s)")
    eliminados = []

    for fila in pendientes:
        nombre   = fila.get("nombre_idea", "?")
        intentos = int(fila.get("intentos", 1))
        ts       = fila.get("timestamp", "")

        if intentos > 3:
            print(f"🗑️ Descartando '{nombre}' — demasiados intentos")
            eliminados.append(ts)
            continue

        try:
            datos = json.loads(fila.get("datos_json", "{}"))
            url   = sync_idea_to_notion(datos)
            if url:
                print(f"✅ Reintento exitoso: '{nombre}'")
                eliminados.append(ts)
            else:
                fila["intentos"] = str(intentos + 1)
                print(f"⚠️ Reintento fallido '{nombre}' — intento {intentos+1}/3")
        except Exception as e:
            print(f"❌ Error '{nombre}': {e}")
            fila["intentos"] = str(intentos + 1)

    # Reescribir CSV sin los procesados
    restantes = [f for f in pendientes if f.get("timestamp") not in eliminados]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        if restantes:
            writer = csv.DictWriter(f, fieldnames=restantes[0].keys())
            writer.writeheader()
            writer.writerows(restantes)
        else:
            f.write("")

    print(f"✅ Cola procesada — {len(eliminados)} sincronizadas, {len(restantes)} pendientes")

def verificar_ideas_sin_sync():
    """Re-intenta sincronizar ideas locales que no llegaron a Notion"""
    ruta_ideas = "data/ideas.json"
    if not os.path.exists(ruta_ideas):
        return

    try:
        with open(ruta_ideas, "r", encoding="utf-8") as f:
            ideas = json.load(f)
    except:
        return

    sin_sync = [i for i in ideas if not i.get("notion_url")]
    if not sin_sync:
        return

    print(f"🔍 {len(sin_sync)} ideas sin sync Notion — reintentando...")

    try:
        from agents.notion_sync_agent import sync_idea_to_notion
    except ImportError:
        return

    actualizadas = False
    for idea in ideas:
        if not idea.get("notion_url"):
            try:
                url = sync_idea_to_notion(idea)
                if url:
                    idea["notion_url"] = url
                    print(f"✅ Sincronizada: {idea.get('nombre','?')}")
                    actualizadas = True
            except Exception as e:
                print(f"⚠️ Error sync '{idea.get('nombre','?')}': {e}")

    if actualizadas:
        with open(ruta_ideas, "w", encoding="utf-8") as f:
            json.dump(ideas, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    procesar_cola()
    verificar_ideas_sin_sync()
    print("✅ run_monitor.py completado")
