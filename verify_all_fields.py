import json

with open('data/ideas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    ultima = data['ideas'][-1]

print("="*80)
print(f"IDEA: {ultima.get('nombre')}")
print("="*80)

# Verificar TODOS los campos de texto
campos = ['nombre', 'problema', 'solucion', 'descripcion', 'propuesta_valor']
for campo in campos:
    valor = ultima.get(campo, '')
    if valor:
        tiene_error = 'Ã' in str(valor)
        status = "❌" if tiene_error else "✅"
        print(f"{status} {campo}: {valor[:80]}")

# Verificar listas
print(f"\n✅ fortalezas: {ultima.get('fortalezas')}")
print(f"✅ debilidades: {ultima.get('debilidades')}")

print("\n" + "="*80)
print("RESULTADO FINAL:")
# Buscar cualquier Ã en todo el objeto
idea_str = json.dumps(ultima, ensure_ascii=False)
if 'Ã©' in idea_str or 'Ã³' in idea_str or 'Ã±' in idea_str or 'Ã¡' in idea_str:
    print("❌ AÚN HAY CARACTERES CORRUPTOS")
else:
    print("✅ TODOS LOS CARACTERES CORRECTOS")
print("="*80)
