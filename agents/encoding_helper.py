"""
Helper para fix de encoding UTF-8
"""

def fix_llm_encoding(text):
    """Detecta y corrige doble encoding UTF-8 si existe"""
    if not text:
        return text
    
    # Detectar si tiene doble encoding buscando patrones típicos
    if 'Ã©' in text or 'Ã³' in text or 'Ã±' in text or 'Ã¡' in text or 'Ã­' in text:
        try:
            # Intentar corregir doble encoding
            return text.encode('latin-1').decode('utf-8')
        except:
            return text
    
    return text
