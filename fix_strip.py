import os

def fix(path, buscar, reemplazar):
    if not os.path.exists(path):
        print(f"SKIP: {path}"); return
    t = open(path, encoding="utf-8").read()
    if buscar not in t:
        print(f"NO ENCONTRADO: {path}"); return
    open(path, "w", encoding="utf-8").write(t.replace(buscar, reemplazar, 1))
    print(f"OK: {path}")

fix("agents/auto_improver.py",
    'texto.split("```json").split("```").strip()[1]',
    'texto.split("```json")[1].split("```")[0].strip()')

fix("agents/auto_improver.py",
    "return str(content).strip() if content else \"\"",
    "c=content; return (c if isinstance(c,str) else ''.join(str(getattr(b,'text',b)) for b in c) if isinstance(c,list) else str(c or '')).strip()")

fix("agents/critic_agent.py",
    "content = response.choices[0].message.content.strip()",
    "raw=response.choices[0].message.content; content=(raw if isinstance(raw,str) else ''.join(str(getattr(b,'text',b)) for b in raw) if isinstance(raw,list) else str(raw or '')).strip()")

fix("agents/generator_agent.py",
    "content = response.choices[0].message.content.strip()",
    "raw=response.choices[0].message.content; content=(raw if isinstance(raw,str) else ''.join(str(getattr(b,'text',b)) for b in raw) if isinstance(raw,list) else str(raw or '')).strip()")

fix("agents/estimation_agent.py",
    "content = response.choices[0].message.content.strip()",
    "raw=response.choices[0].message.content; content=(raw if isinstance(raw,str) else ''.join(str(getattr(b,'text',b)) for b in raw) if isinstance(raw,list) else str(raw or '')).strip()")

fix("agents/report_generator.py",
    "opinion = response.choices[0].message.content.strip()",
    "raw=response.choices[0].message.content; opinion=(raw if isinstance(raw,str) else ''.join(str(getattr(b,'text',b)) for b in raw) if isinstance(raw,list) else str(raw or '')).strip()")

fix("agents/trend_hunter_agent.py",
    "content = content.split('```json').split('```').strip()[1]",
    "content = content.split('```json')[1].split('```')[0].strip()")

fix("agents/competition_agent.py",
    "content = response.choices.message.content.strip()",
    "raw=response.choices[0].message.content if hasattr(response,'choices') and response.choices else ''; content=(raw if isinstance(raw,str) else ''.join(str(getattr(b,'text',b)) for b in raw) if isinstance(raw,list) else str(raw or '')).strip()")

fix("agents/groq_shared.py",
    'texto = partes[1].split("```").strip()',
    'texto = partes[1].split("```")[0].strip()')

print("Listo.")
