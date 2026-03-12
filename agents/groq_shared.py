"""
groq_shared.py - Cliente Groq compartido e inmune a cambios de SDK.
Todos los agentes deben importar llamar_groq desde aqui.
"""
import os, json, time, re

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MODELOS_GROQ = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]

def _content_to_str(content):
    """Convierte CUALQUIER tipo devuelto por Groq SDK a string puro."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        partes = []
        for bloque in content:
            if isinstance(bloque, str):
                partes.append(bloque)
            elif isinstance(bloque, dict):
                partes.append(str(bloque.get("text", bloque.get("content", ""))))
            elif hasattr(bloque, "text"):
                partes.append(str(bloque.text))
            elif hasattr(bloque, "content"):
                partes.append(str(bloque.content))
            else:
                partes.append(str(bloque))
        return "".join(partes)
    if isinstance(content, dict):
        return str(content.get("text", content.get("content", str(content))))
    if hasattr(content, "text"):
        return str(content.text)
    if hasattr(content, "content"):
        return str(content.content)
    return str(content)

def _extraer_texto_respuesta(resp):
    """Extrae el texto de una respuesta Groq sea cual sea su estructura."""
    choices = None
    if hasattr(resp, "choices"):
        choices = resp.choices
    elif isinstance(resp, dict):
        choices = resp.get("choices", [])
    elif isinstance(resp, (list, tuple)):
        choices = resp

    if not choices:
        return _content_to_str(resp)

    try:
        choice = choices[0]
    except (IndexError, TypeError):
        return ""

    # choice.message.content
    if hasattr(choice, "message"):
        msg = choice.message
        if hasattr(msg, "content"):
            return _content_to_str(msg.content)
        if isinstance(msg, dict):
            return _content_to_str(msg.get("content", ""))
        if isinstance(msg, (list, str)):
            return _content_to_str(msg)

    # choice es dict
    if isinstance(choice, dict):
        msg = choice.get("message", {})
        if isinstance(msg, dict):
            return _content_to_str(msg.get("content", ""))
        return _content_to_str(msg or choice.get("content", ""))

    # choice.text / choice.content directo
    if hasattr(choice, "text") and choice.text:
        return _content_to_str(choice.text)
    if hasattr(choice, "content") and choice.content:
        return _content_to_str(choice.content)

    # delta (streaming accidental)
    if hasattr(choice, "delta"):
        delta = choice.delta
        if hasattr(delta, "content") and delta.content:
            return _content_to_str(delta.content)

    # fallback
    return _content_to_str(choice)

def llamar_groq(prompt, max_tokens=2000, sistema=None, temperatura=None, modelos=None):
    """
    Llama a Groq con reintentos y fallback de modelos.
    Siempre devuelve str o lanza RuntimeError.
    """
    if temperatura is None:
        temperatura = float(os.environ.get("GROQ_TEMPERATURA", "0.85"))
    if modelos is None:
        modelos = MODELOS_GROQ
    if sistema is None:
        sistema = "Eres un asistente experto. Responde solo con JSON valido."

    messages = [
        {"role": "system", "content": sistema},
        {"role": "user",   "content": prompt},
    ]

    try:
        import groq
    except ImportError:
        raise RuntimeError("groq SDK no instalado")

    for modelo in modelos:
        for intento in range(2):
            try:
                client = groq.Groq(api_key=GROQ_API_KEY, timeout=90)
                resp   = client.chat.completions.create(
                    model       = modelo,
                    messages    = messages,
                    max_tokens  = max_tokens,
                    temperature = temperatura,
                )
                texto = _extraer_texto_respuesta(resp).strip()
                if texto:
                    return texto

            except Exception as e:
                err = str(e).lower()
                if any(x in err for x in ["rate", "429", "too many"]):
                    wait = 15 + intento * 10
                    try:
                        m = re.search(r'retry.after["\s:]+(\d+)', err)
                        if m: wait = min(int(m.group(1)) + 2, 30)
                    except: pass
                    time.sleep(wait)
                    continue
                elif any(x in err for x in ["not found", "404", "422", "invalid model", "decommission"]):
                    break  # modelo no disponible, siguiente
                else:
                    break  # otro error, siguiente modelo
        # siguiente modelo

    raise RuntimeError("Ningun modelo Groq disponible")

def limpiar_json(texto):
    """Extrae JSON valido de un string."""
    if not isinstance(texto, str):
        texto = _content_to_str(texto)
    texto = texto.strip()
    if not texto:
        return "{}"
    if "```json" in texto:
        partes = texto.split("```json")
        if len(partes) > 1:
            texto = partes[1].split("```")[0].strip()
    elif "```" in texto:
        for parte in texto.split("```"):
            parte = parte.strip()
            if parte.startswith("{"):
                texto = parte
                break
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        return texto[inicio:fin+1]
    return texto

# fin agents/groq_shared.py
