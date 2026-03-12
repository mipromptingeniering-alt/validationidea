"""
fix_all_strip_bugs.py
Parchea todos los archivos con .strip() sobre listas.
Ejecuta: python fix_all_strip_bugs.py
"""
import os, re

FIXES = {
    "agents/auto_improver.py": [
        (
            "texto = texto.split(\"```json\").split(\"```\").strip()[1]",
            "texto = texto.split(\"```json\")[1].split(\"```\")[0].strip()"
        ),
        (
            "return str(content).strip() if content else \"\"",
            "return str(content).strip() if content and not isinstance(content, list) else (str(content[0].text if hasattr(content[0], 'text') else content[0]) if isinstance(content, list) and content else \"\")"
        ),
    ],
    "agents/competition_agent.py": [
        (
            "content = response.choices.message.content.strip()",
            "choices = response.choices if hasattr(response, 'choices') else []\nchoice = choices[0] if choices else None\nmsg = getattr(choice, 'message', None) if choice else None\nraw = getattr(msg, 'content', '') if msg else ''\ncontent = (raw if isinstance(raw, str) else (''.join(str(b.text if hasattr(b,'text') else b) for b in raw) if isinstance(raw, list) else str(raw or ''))).strip()"
        ),
    ],
    "agents/critic_agent.py": [
        (
            "content = response.choices[0].message.content.strip()",
            "raw = response.choices[0].message.content\ncontent = (raw if isinstance(raw, str) else (''.join(str(b.text if hasattr(b,'text') else b) for b in raw) if isinstance(raw, list) else str(raw or ''))).strip()"
        ),
    ],
    "agents/generator_agent.py": [
        (
            "content = response.choices[0].message.content.strip()",
            "raw = response.choices[0].message.content\ncontent = (raw if isinstance(raw, str) else (''.join(str(b.text if hasattr(b,'text') else b) for b in raw) if isinstance(raw, list) else str(raw or ''))).strip()"
        ),
    ],
    "agents/estimation_agent.py": [
        (
            "content = response.choices[0].message.content.strip()",
            "raw = response.choices[0].message.content\ncontent = (raw if isinstance(raw, str) else (''.join(str(b.text if hasattr(b,'text') else b) for b in raw) if isinstance(raw, list) else str(raw or ''))).strip()"
        ),
    ],
    "agents/report_generator.py": [
        (
            "opinion = response.choices[0].message.content.strip()",
            "raw = response.choices[0].message.content\nopinion = (raw if isinstance(raw, str) else (''.join(str(b.text if hasattr(b,'text') else b) for b in raw) if isinstance(raw, list) else str(raw or ''))).strip()"
        ),
    ],
    "agents/trend_hunter_agent.py": [
        (
            "content = content.split('```json').split('```').strip()[1]",
            "content = content.split('```json')[1].split('```')[0].strip()"
        ),
        (
            "content = content.split('```').split('```')[0].strip()",
            "content = content.split('```')[1].split('```')[0].strip() if content.count('```') >= 2 else content.strip()"
        ),
    ],
    "agents/groq_shared.py": [
        (
            "texto = partes[1].split(\"```\").strip()",
            "texto = partes[1].split(\"```\").strip()"
        ),
    ],
}

def parchear(filepath, buscar, reemplazar):
    if not os.path.exists(filepath):
        print(f"  SKIP (no existe): {filepath}")
        return False
    with open(filepath, "r", encoding="utf-8") as f:
        contenido = f.read()
    if buscar not in contenido:
        print(f"  SKIP (no encontrado): {filepath}")
        return False
    nuevo = contenido.replace(buscar, reemplazar, 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(nuevo)
    print(f"  OK: {filepath}")
    return True

if __name__ == "__main__":
    print("Parcheando archivos con .strip() sobre listas...\n")
    total = 0
    for archivo, cambios in FIXES.items():
        for buscar, reemplazar in cambios:
            if parchear(archivo, buscar, reemplazar):
                total += 1
    print(f"\nTotal parches aplicados: {total}")
    print("Ahora ejecuta: git add -A && git commit -m 'fix: strip sobre lista en 7 agentes' && git push")
