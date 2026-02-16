import json
with open('data/ideas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    prospectaflow = None
    for idea in data['ideas']:
        if 'Prospectaflow' in idea.get('nombre', ''):
            prospectaflow = idea
            break
    
    if prospectaflow:
        print("\n=== DESPUÉS DE LIMPIAR ===")
        print(f"problema: {prospectaflow.get('problema')}")
        print(f"Bytes: {prospectaflow.get('problema').encode('utf-8')}")
