import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def _texto_a_bloques(texto):
    """Convierte texto con ## ### - * 1. en bloques de Notion."""
    bloques = []
    for linea in texto.split("\n"):
        linea_strip = linea.strip()
        if not linea_strip:
            continue

        if linea_strip.startswith("## "):
            titulo = linea_strip[3:].strip()[:2000]
            bloques.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": titulo}}]
                },
            })
        elif linea_strip.startswith("### "):
            titulo = linea_strip[4:].strip()[:2000]
            bloques.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": titulo}}]
                },
            })
        elif linea_strip.startswith(("- ", "* ", "• ")):
            contenido = linea_strip[2:].strip()[:2000]
            bloques.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": contenido}}]
                },
            })
        elif len(linea_strip) > 1 and linea_strip[0].isdigit() and linea_strip[1] in (".", ")"):
            contenido = linea_strip[2:].strip()[:2000]
            bloques.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": contenido}}]
                },
            })
        else:
            contenido = linea_strip[:2000]
            bloques.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": contenido}}]
                },
            })

    return bloques


def _enviar_bloques(page_id, bloques):
    """Envía bloques en lotes de 100 (límite de Notion)."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    total = len(bloques)
    enviados = 0

    for i in range(0, total, 100):
        lote = bloques[i: i + 100]
        r = requests.patch(url, headers=HEADERS, json={"children": lote}, timeout=30)
        if r.status_code == 200:
            enviados += len(lote)
            print(f"   📦 Bloques enviados: {enviados}/{total}")
        else:
            print(f"   ❌ Error enviando bloques: {r.status_code} — {r.text[:200]}")
            return False
        time.sleep(0.5)

    return True


def _marcar_informe_completo(page_id):
    """Marca la propiedad 'Informe Completo' para no reprocesar."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Informe Completo": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "Generado automaticamente"}
                }]
            }
        }
    }
    r = requests.patch(url, headers=HEADERS, json=payload, timeout=15)
    if r.status_code == 200:
        print("   ✅ Marcado como 'Informe Completo'")
        return True
    else:
        print(f"   ❌ Error marcando informe: {r.status_code}")
        return False


def _limpiar_bloques_existentes(page_id):
    """Obtiene y elimina los bloques actuales de la página."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return
    bloques = r.json().get("results", [])
    for bloque in bloques:
        bid = bloque.get("id")
        if bid:
            requests.delete(
                f"https://api.notion.com/v1/blocks/{bid}",
                headers=HEADERS,
                timeout=10,
            )
            time.sleep(0.1)


def write_report_to_notion(page_id, informe_texto, limpiar=False):
    """Escribe el informe completo como bloques en la página de Notion."""
    print(f"   📄 Escribiendo informe en página {page_id[:8]}...")

    if limpiar:
        print("   🧹 Limpiando bloques existentes...")
        _limpiar_bloques_existentes(page_id)

    bloques = _texto_a_bloques(informe_texto)
    print(f"   🔢 Total bloques generados: {len(bloques)}")

    exito = _enviar_bloques(page_id, bloques)

    if exito:
        _marcar_informe_completo(page_id)
        print(f"   ✅ Informe escrito correctamente ({len(bloques)} bloques)")
        return True
    else:
        print("   ❌ Error escribiendo informe")
        return False
