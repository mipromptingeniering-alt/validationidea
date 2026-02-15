"""
Learning Agent: auto-mejora cada 3 ideas.
"""
import json
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def learn_and_improve():
    """Analiza últimas 3 ideas y optimiza"""
    
    print("🧠 Analizando...")
    
    try:
        with open('data/ideas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        last_3 = data['ideas'][-3:]
        if len(last_3) < 3:
            print("⏳ Esperando más ideas")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Análisis
    summary = []
    for idea in last_3:
        summary.append({
            'nombre': idea.get('nombre'),
            'score': idea.get('score_critico', 0),
            'viral': idea.get('viral_score', 0),
            'fuertes': idea.get('critique', {}).get('puntos_fuertes', []),
            'debiles': idea.get('critique', {}).get('puntos_debiles', [])
        })
    
    prompt = f"""Analiza estas 3 ideas y genera reglas de mejora:

{json.dumps(summary, indent=2, ensure_ascii=False)}

Responde en JSON:
{{
  "patrones_exitosos": ["..."],
  "errores": ["..."],
  "reglas": ["REGLA específica 1", "REGLA 2", "REGLA 3"]
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # Guardar
        log_file = 'data/learning_log.json'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = {'iterations': []}
        
        log['iterations'].append({
            'date': str(datetime.now()),
            'total_ideas': len(data['ideas']),
            'analysis': analysis
        })
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(analysis.get('reglas', []))} reglas nuevas")
        
    except Exception as e:
        print(f"❌ Learning error: {e}")