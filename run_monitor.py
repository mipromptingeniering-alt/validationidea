import os
import sys
import json

os.environ["PYTHONUTF8"] = "1"

def main():
    print("📄 run_monitor.py — procesando cola y pendientes...")

    # Procesar cola CSV (reintentos de Notion)
    try:
        from agents.cola_csv import obtener_pendientes, eliminar_de_cola, incrementar_intentos
        from agents.notion_sync_agent import sync_idea_to_notion
        pendientes = obtener_pendientes()
        if pendientes:
            print(f"📋 Cola CSV: {len(pendientes)} pendiente(s)")
            for fila in pendientes:
                ts = fila.get("timestamp", "")
                nombre = fila.get("nombre_idea", "?")
                intentos = int(fila.get("intentos", 1))
                if intentos > 3:
                    print(f"⏭️ Descartando '{nombre}' (>3 intentos)")
                    eliminar_de_cola(ts)
                    continue
                try:
                    datos = json.loads(fila.get("datos_json", "{}"))
                    resultado = sync_idea_to_notion(datos)
                    if resultado:
                        print(f"✅ Reintento exitoso: '{nombre}'")
                        eliminar_de_cola(ts)
                    else:
                        incrementar_intentos(ts)
                except Exception as e:
                    print(f"❌ Fallo reintento '{nombre}': {e}")
                    incrementar_intentos(ts)
        else:
            print("✅ Cola CSV vacía")
    except Exception as e:
        print(f"⚠️ Error cola CSV: {e}")

    print("✅ run_monitor.py completado")

if __name__ == "__main__":
    main()
