import os
import time
from notion_client import Client


def update_informe_completo(page_id, report_text, idea_nombre=""):
    """Marca la propiedad y escribe el informe como bloques en la pagina"""
    notion = Client(auth=os.environ.get("NOTION_TOKEN"))

    # 1. Marcar propiedad para no reprocesar
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Informe Completo": {
                    "rich_text": [{"text": {"content": "Generado automaticamente"}}]
                }
            },
        )
        print(f"✅ Propiedad 'Informe Completo' marcada: {idea_nombre}")
    except Exception as e:
        print(f"⚠️  Error marcando propiedad: {e}")

    # 2. Convertir texto a bloques Notion
    blocks = text_to_notion_blocks(report_text)
    total = len(blocks)

    # 3. Enviar en lotes de 100 (limite de Notion)
    written = 0
    for i in range(0, total, 100):
        batch = blocks[i: i + 100]
        try:
            notion.blocks.children.append(block_id=page_id, children=batch)
            written += len(batch)
            print(f"📝 Bloques: {written}/{total}")
            time.sleep(0.4)
        except Exception as e:
            print(f"⚠️  Error lote {i // 100 + 1}: {e}")
            time.sleep(2)

    print(f"✅ Informe escrito: {written}/{total} bloques en Notion")
    return written


def text_to_notion_blocks(text):
    """Convierte markdown a bloques de Notion"""
    blocks = []
    for line in text.split("\n"):
        s = line.strip()

        if not s:
            blocks.append({"object": "block", "type": "paragraph",
                            "paragraph": {"rich_text": []}})

        elif s.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                            "heading_2": {"rich_text": [
                                {"type": "text", "text": {"content": s[3:][:2000]}}
                            ]}})

        elif s.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                            "heading_3": {"rich_text": [
                                {"type": "text", "text": {"content": s[4:][:2000]}}
                            ]}})

        elif s.startswith(("- ", "* ")):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": [
                                {"type": "text", "text": {"content": s[2:][:2000]}}
                            ]}})

        elif len(s) > 1 and s[0].isdigit() and s[1] in ".)" and len(s) > 2:
            blocks.append({"object": "block", "type": "numbered_list_item",
                            "numbered_list_item": {"rich_text": [
                                {"type": "text", "text": {"content": s[2:].strip()[:2000]}}
                            ]}})

        else:
            # Cortar parrafos largos en chunks de 2000
            chunks = [s[i: i + 2000] for i in range(0, len(s), 2000)]
            for chunk in chunks:
                blocks.append({"object": "block", "type": "paragraph",
                                "paragraph": {"rich_text": [
                                    {"type": "text", "text": {"content": chunk}}
                                ]}})
    return blocks
