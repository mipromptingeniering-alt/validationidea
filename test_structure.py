import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    if data['ideas']:
        idea = data['ideas'][-1]
        print("\n" + "="*60)
        print("ESTRUCTURA COMPLETA (PRIMEROS 1000 CHARS):")
        print("="*60)
        print(json.dumps(idea, indent=2, ensure_ascii=False)[:1000])
