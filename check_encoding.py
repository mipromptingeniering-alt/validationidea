import json
import sys

print(f"Default encoding: {sys.getdefaultencoding()}")

# Leer JSON
with open('data/ideas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

prospectaflow = None
for idea in data['ideas']:
    if 'Prospectaflow' in idea.get('nombre', ''):
        prospectaflow = idea
        break

if prospectaflow:
    print("\n=== CARACTERES EN JSON ===")
    for key in ['fortalezas', 'debilidades', 'problema', 'solucion']:
        value = prospectaflow.get(key)
        print(f"{key}: {value}")
        if isinstance(value, str):
            print(f"  Bytes: {value.encode('utf-8')}")
