import json
with open('data/ideas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    ultima = data['ideas'][-1]
    
    print("\n" + "="*80)
    print(f"ÚLTIMA IDEA: {ultima.get('nombre')}")
    print("="*80)
    print(f"problema: {ultima.get('problema')}")
    print(f"Bytes: {ultima.get('problema', '').encode('utf-8')}")
    
    # Verificar si tiene caracteres corruptos
    problema_str = ultima.get('problema', '')
    if '\xc3\x83' in problema_str or 'Ã³' in problema_str or 'Ã¡' in problema_str:
        print("\n❌ AÚN HAY DOBLE ENCODING")
    else:
        print("\n✅ ENCODING CORRECTO")
    print("="*80)
