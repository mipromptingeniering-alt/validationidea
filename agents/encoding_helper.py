"""
Helper para fix de encoding UTF-8
"""
import json

def fix_llm_encoding(text):
    """Detecta y corrige doble encoding UTF-8 si existe"""
    if not text:
        return text
    
    # Si es bytes, decodificar primero
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    
    # Convertir a string si no lo es
    text = str(text)
    
    # Detectar si tiene doble encoding buscando patrones típicos
    if 'Ã©' in text or 'Ã³' in text or 'Ã±' in text or 'Ã¡' in text or 'Ã­' in text:
        try:
            # Intentar corregir doble encoding
            return text.encode('latin-1').decode('utf-8')
        except:
            return text
    
    return text
