with open('agents/critic_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

def fix_text(text):
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
        text = text.replace(old, new)
    return text

cleaned = fix_text(content)

with open('agents/critic_agent.py', 'w', encoding='utf-8') as f:
    f.write(cleaned)

print("✅ critic_agent.py limpiado")
