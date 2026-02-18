import json

with open('data/ideas.json', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Ã©': 'é',
    'Ã³': 'ó',
    'Ã±': 'ñ',
    'Ã¡': 'á',
    'Ã­': 'í',
    'Ãº': 'ú',
    'â‚¬': '€',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('data/ideas.json', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ ideas.json limpiado")
