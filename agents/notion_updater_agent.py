import os
import time
import requests

NOTION_API_KEY = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
NOTION_VERSION = "2022-06-28"


def _h():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _rt(texto: str) -> list:
    """Divide en chunks de 2000 chars (límite de Notion por bloque)."""
    chunks = [texto[i:i+2000] for i in range(0, len(texto), 2000)]
    return [{"type": "text", "text": {"content": c}} for c in chunks] or [
        {"type": "text", "text": {"content": ""}}
    ]


def texto_a_bloques(texto: str) -> list:
    bloques = []
    for linea in texto.split("\n"):
        linea = linea.rstrip()
        if not linea:
            continue
        if linea.startswith("## "):
            bloques.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": _rt(linea[3:])}
            })
        elif linea.startswith("### "):
            bloques.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": _rt(linea[4:])}
            })
        elif linea.startswith(("- ", "* ")):
            bloques.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rt(linea[2:])}
            })
        elif len(linea) > 2 and linea[0].isdigit() and linea[1] in ".)":
            bloques.append({
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": _rt(linea[2:].strip())}
            })
        else:
            bloques.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": _rt(linea)}
            })
    return bloques


def marcar_informe_completo(page_id: str) -> bool:
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Informe Completo": {
                "rich_text": [{"type": "text", "text": {"content": "Generado automaticamente"}}]
            }
        }
    }
    r = requests.patch(url, headers=_h(), json=payload, timeout=30)
    ok = r.status_code == 200
    if not ok:
        print(f"[NotionUpdater] Error marcando bandera: {r.status_code} {r.text[:200]}")
    return ok


def escribir_bloques(page_id: str, bloques: list) -> int:
    """Envía en lotes de 100 — límite oficial Notion API."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    total = len(bloques)
    escritos = 0
    for i in range(0, total, 100):
        lote = bloques[i:i+100]
        r = requests.patch(url, headers=_h(), json={"children": lote}, timeout=30)
        if r.status_code == 200:
            escritos += len(lote)
            print(f"[NotionUpdater] Bloques: {escritos}/{total}")
        else:
            print(f"[NotionUpdater] Error lote {i//100+1}: {r.status_code} {r.text[:300]}")
            time.sleep(3)
        time.sleep(0.5)
    return escritos


def write_report_to_notion(page_id: str, texto_informe: str) -> int:
    pid = page_id.replace("-", "")
    print(f"[NotionUpdater] Procesando página: {pid}")
    marcar_informe_completo(pid)
    bloques = texto_a_bloques(texto_informe)
    print(f"[NotionUpdater] Total bloques: {len(bloques)}")
    escritos = escribir_bloques(pid, bloques)
    print(f"[NotionUpdater] ✅ {escritos}/{len(bloques)} bloques escritos")
    return escritos
