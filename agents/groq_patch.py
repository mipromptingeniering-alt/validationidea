@'
"""
groq_patch.py - Parchea el SDK de Groq a nivel global.
Importar al inicio de monitor_nocturno.py y run_batch.py.
Garantiza que choice.message.content sea SIEMPRE string.
"""
try:
    import groq.resources.chat.completions as _gcc

    _original_create = _gcc.Completions.create

    def _patched_create(self, *args, **kwargs):
        resp = _original_create(self, *args, **kwargs)
        try:
            if hasattr(resp, "choices"):
                for choice in (resp.choices or []):
                    msg = getattr(choice, "message", None)
                    if msg is None:
                        continue
                    c = getattr(msg, "content", None)
                    if isinstance(c, str):
                        continue
                    if isinstance(c, list):
                        msg.content = "".join(
                            str(b.text if hasattr(b, "text") else
                                b.get("text", b.get("content", str(b)))
                                if isinstance(b, dict) else b)
                            for b in c
                        )
                    elif c is not None:
                        msg.content = str(c)
                    else:
                        msg.content = ""
        except Exception as e:
            print(f"[groq_patch] warning: {e}")
        return resp

    _gcc.Completions.create = _patched_create
    print("[groq_patch] SDK Groq parcheado OK")

except Exception as e:
    print(f"[groq_patch] no aplicado: {e}")
'@ | Out-File -FilePath agents/groq_patch.py -Encoding utf8
