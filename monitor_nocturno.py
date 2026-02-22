import os
import time
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_API_KEY      = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID  = os.environ.get("NOTION_DATABASE_ID")
NOTION_VERSION      = "2022-06-28"

# ─── Intervalos ───────────────────────────────────────────────
INTERVALO_GENERAR   = 30 * 60   # genera idea nueva cada 30 min
INTERVALO_INFORMES  =  5 * 60   # revisa informes pendientes cada 5 min


def telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"[Telegram] Error: {e}")


def ejecutar(script: str, timeout: int = 600) -> str:
    try:
        res = subprocess.run(
            ["python", script],
            capture_output=True, text=True, timeout=timeout, encoding="utf-8"
        )
        salida = (res.stdout + res.stderr)
        return salida[-2000:] if len(salida) > 2000 else salida
    except subprocess.TimeoutExpired:
        return f"TIMEOUT tras {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


def _h():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def get_todas_ideas() -> list:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    ideas, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        try:
            r = requests.post(url, headers=_h(), json=body, timeout=30)
            data = r.json()
            ideas.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        except Exception as e:
            print(f"[Monitor] Error Notion: {e}")
            break
    return ideas


def get_ideas_sin_informe() -> list:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    ideas, cursor = [], None
    while True:
        body = {
            "page_size": 100,
            "filter": {"property": "Informe Completo", "rich_text": {"is_empty": True}}
        }
        if cursor:
            body["start_cursor"] = cursor
        try:
            r = requests.post(url, headers=_h(), json=body, timeout=30)
            data = r.json()
            ideas.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        except Exception as e:
            print(f"[Monitor] Error sin_informe: {e}")
            break
    return ideas


def nombre_idea(page: dict) -> str:
    t = page.get("properties", {}).get("Name", {}).get("title", [])
    return t[0]["plain_text"] if t else "Sin nombre"


def url_idea(page: dict) -> str:
    return f"https://notion.so/{page['id'].replace('-', '')}"


def resumen_diario():
    ideas   = get_todas_ideas()
    total   = len(ideas)
    con_inf = sum(
        1 for i in ideas
        if i.get("properties", {}).get("Informe Completo", {}).get("rich_text")
    )
    scores = [
        i["properties"]["ScoreGen"]["number"]
        for i in ideas
        if i.get("properties", {}).get("ScoreGen", {}).get("number") is not None
    ]
    avg = round(sum(scores) / len(scores), 1) if scores else 0

    # Auto-aprendizaje: incluir insights de KB
    try:
        from agents.knowledge_base import get_stats
        kb = get_stats()
        kb_texto = (
            f"\n🧠 <b>Auto-aprendizaje:</b>\n"
            f"  Ideas analizadas: {kb['total']}\n"
            f"  Exitosas (score>75): {kb['exitosas']}\n"
            f"  Mejor tipo: {kb['mejor_tipo']}\n"
            f"  Mejor vertical: {kb['mejor_vertical']}"
        )
    except Exception:
        kb_texto = ""

    telegram(
        f"📊 <b>Resumen {datetime.now().strftime('%d/%m/%Y')}</b>\n"
        f"💡 Total ideas: <b>{total}</b>\n"
        f"✅ Con informe: <b>{con_inf}</b>\n"
        f"⏳ Pendientes: <b>{total - con_inf}</b>\n"
        f"⭐ Score medio: <b>{avg}/100</b>"
        + kb_texto
    )


def main():
    telegram(
        "🚀 <b>Monitor nocturno iniciado</b>\n"
        "• 💡 Nueva idea cada 30 min\n"
        "• 📝 Informes cada 5 min\n"
        "• 📊 Resumen diario 08:00\n"
        "• 🌙 Mantenimiento 03:00\n"
        "• 🧠 Auto-aprendizaje activo"
    )

    ts_ultima_idea     = 0
    ts_ultimo_informe  = 0
    ultimo_dia_resumen = -1
    ultima_hora_mant   = -1
    seen_ids = {p["id"] for p in get_todas_ideas()}
    print(f"[Monitor] Iniciado. {len(seen_ids)} ideas existentes en Notion.")

    while True:
        try:
            ahora = datetime.now()
            ts    = time.time()

            # ─── Cada 5 min: nuevas ideas + informes pendientes ───────
            if ts - ts_ultimo_informe >= INTERVALO_INFORMES:
                ts_ultimo_informe = ts
                todas = get_todas_ideas()

                for p in todas:
                    if p["id"] not in seen_ids:
                        seen_ids.add(p["id"])
                        telegram(
                            f"💡 <b>Nueva idea detectada:</b> {nombre_idea(p)}\n"
                            f"{url_idea(p)}"
                        )

                sin_inf = get_ideas_sin_informe()
                if sin_inf:
                    n = len(sin_inf)
                    print(f"[Monitor] {n} ideas sin informe → lanzando run_monitor.py")
                    telegram(f"📝 <b>{n} ideas sin informe.</b> Generando ahora...")
                    out = ejecutar("run_monitor.py", timeout=600)
                    aun_pend = len(get_ideas_sin_informe())
                    generados = n - aun_pend
                    telegram(
                        f"✅ <b>{generados} informes generados.</b>\n"
                        f"Aún pendientes: {aun_pend}"
                    )
                    print(f"[Monitor] Informes: {out[-400:]}")

            # ─── Cada 30 min: generar idea nueva ─────────────────────
            if ts - ts_ultima_idea >= INTERVALO_GENERAR:
                ts_ultima_idea = ts
                print("[Monitor] Auto-generando idea nueva...")
                telegram("🤖 <b>Generando idea nueva automáticamente...</b>")
                out = ejecutar("run_batch.py", timeout=120)
                if "traceback" in out.lower() or "error" in out.lower():
                    telegram(f"⚠️ <b>Error en run_batch:</b>\n<code>{out[-400:]}</code>")
                else:
                    print(f"[Monitor] Idea OK: {out[-200:]}")

            # ─── 08:00 Resumen diario ─────────────────────────────────
            if ahora.hour == 8 and ahora.day != ultimo_dia_resumen:
                ultimo_dia_resumen = ahora.day
                resumen_diario()

            # ─── 03:00 Mantenimiento nocturno ─────────────────────────
            if ahora.hour == 3 and ahora.hour != ultima_hora_mant:
                ultima_hora_mant = ahora.hour
                telegram("🌙 <b>Mantenimiento nocturno iniciado</b>")
                ejecutar("completar_campos.py", timeout=600)
                ejecutar("run_monitor.py", timeout=600)
                telegram("✅ <b>Mantenimiento completado.</b> Todo al día.")

        except Exception as e:
            print(f"[Monitor] Error en bucle principal: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
