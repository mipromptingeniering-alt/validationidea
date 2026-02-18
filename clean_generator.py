with open('agents/generator_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Función para limpiar doble encoding
def fix_text(text):
    replacements = {
        'Ã©': 'é',
        'Ã³': 'ó',
        'Ã±': 'ñ',
        'Ã¡': 'á',
        'Ã­': 'í',
        'Ãº': 'ú',
        'â‚¬': '€',
        'Ã': 'í',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# Limpiar todo el contenido
cleaned = fix_text(content)

# Guardar
with open('agents/generator_agent.py', 'w', encoding='utf-8') as f:
    f.write(cleaned)

print("✅ generator_agent.py limpiado")
