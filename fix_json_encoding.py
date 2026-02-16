import json

# Leer JSON corrupto
with open('data/ideas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Función para limpiar strings con doble encoding
def fix_encoding(obj):
    if isinstance(obj, dict):
        return {k: fix_encoding(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_encoding(item) for item in obj]
    elif isinstance(obj, str):
        try:
            # Intentar decodificar doble encoding
            # UTF-8 → Latin-1 → UTF-8 se arregla así:
            return obj.encode('latin-1').decode('utf-8')
        except:
            return obj
    return obj

# Limpiar todas las ideas
data_limpia = fix_encoding(data)

# Guardar correctamente
with open('data/ideas.json', 'w', encoding='utf-8') as f:
    json.dump(data_limpia, f, indent=2, ensure_ascii=False)

print("✅ JSON limpiado y guardado con UTF-8 correcto")
