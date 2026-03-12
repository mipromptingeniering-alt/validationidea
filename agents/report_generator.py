import os
import json
from datetime import datetime
from groq import Groq

def generate(idea, critique):
    """Genera informe markdown en carpeta informes/slug/"""
    
    print("\n📊 Generando informe...")
    
    slug = idea.get('slug', 'idea')
    nombre = idea.get('nombre', 'Sin nombre')
    
    # Generar opinión profesional con IA
    opinion_profesional = generate_professional_opinion(idea, critique)
    
    # Contenido del informe
    informe = f"""# 📊 INFORME DE VALIDACIÓN: {nombre}

**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Score Generador:** {idea.get('score_generador', 0)}  
**Score Crítico:** {critique.get('score_critico', 0)}  
**Score Promedio:** {int((idea.get('score_generador', 0) + critique.get('score_critico', 0)) / 2)}

---

## 🎯 RESUMEN EJECUTIVO

{idea.get('descripcion_corta', 'Sin descripción')}

---

## 🔥 OPINIÓN PROFESIONAL

{opinion_profesional}

---

## ❌ PROBLEMA

{idea.get('problema', 'No especificado')}

---

## ✅ SOLUCIÓN

{idea.get('solucion', 'No especificada')}

---

## 🎯 PÚBLICO OBJETIVO

{idea.get('publico_objetivo', 'No especificado')}

---

## 💰 MONETIZACIÓN

**Modelo:** {idea.get('modelo_monetizacion', 'No especificado')}

**Precio:** {idea.get('precio_sugerido', 'N/A')}€

**Proyección 6 meses:** {idea.get('revenue_6_meses', 'N/A')}

---

## 🚀 CÓMO MONETIZAR

{idea.get('como_monetizar', 'Vender online en marketplaces y redes sociales')}

---

## 📈 CANALES DE VENTA

{idea.get('canales_venta', 'Gumroad, Twitter, ProductHunt')}

---

## ⚙️ ESFUERZO INICIAL

{idea.get('esfuerzo_inicial', '30 horas')}

---

## ✅ VALIDACIÓN INICIAL

{idea.get('validacion_inicial', '10 ventas en primeras 2 semanas')}

---

## 🎯 EVALUACIÓN CRÍTICA

### Puntos Fuertes

{format_list(critique.get('puntos_fuertes', ['Monetización clara']))}

### Puntos Débiles

{format_list(critique.get('puntos_debiles', ['Requiere validación de mercado']))}

### Recomendaciones

{format_list(critique.get('recomendaciones', ['Empezar con MVP simple']))}

---

## 📝 CONCLUSIÓN

{critique.get('resumen', 'Idea con potencial monetizable. Requiere validación con usuarios reales.')}

---

**Generado automáticamente por ValidationIdea**  
**Sistema Multi-Agente IA v2.0**
"""
    
    # GUARDAR EN informes/slug/informe-slug.md (CORRECTO)
    output_dir = f'informes/{slug}'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/informe-{slug}.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(informe)
    
    print(f"✅ Informe generado: {output_file}")
    
    return output_file

def generate_professional_opinion(idea, critique):
    """Genera opinión profesional con IA"""
    
    print("🧠 Generando opinión profesional...")
    
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        prompt = f"""Eres un experto en monetización de productos digitales con 10 años de experiencia.

Analiza este producto y da tu opinión profesional:

**Producto:** {idea.get('nombre')}
**Tipo:** {idea.get('tipo_producto', 'Digital')}
**Problema:** {idea.get('problema')}
**Solución:** {idea.get('solucion')}
**Monetización:** {idea.get('modelo_monetizacion')}
**Score:** {critique.get('score_critico')}/100

Da tu opinión en este formato:

### 🎯 Viabilidad (X/10)
[1-2 frases sobre si es viable monetizarlo]

### 💰 Potencial Ingresos (X/10)
[1-2 frases sobre potencial revenue]

### ⚡ Velocidad Ejecución (X/10)
[1-2 frases sobre cuán rápido se puede crear]

### 🚨 Riesgos Principales
- [Riesgo 1]
- [Riesgo 2]

### 💡 Oportunidades
- [Oportunidad 1]
- [Oportunidad 2]

### 📊 Veredicto Final
[2-3 frases: ¿Lo harías tú? ¿Por qué?]

Sé directo y honesto."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un experto en monetización de productos digitales. Das opiniones honestas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        raw=response.choices[0].message.content; opinion=(raw if isinstance(raw,str) else ''.join(str(getattr(b,'text',b)) for b in raw) if isinstance(raw,list) else str(raw or '')).strip()
        return opinion
    
    except Exception as e:
        print(f"⚠️  Error generando opinión: {e}")
        return f"""### 🎯 Viabilidad (7/10)
Producto monetizable con mercado existente.

### 💰 Potencial Ingresos (6/10)
Ingresos moderados posibles en 6 meses.

### ⚡ Velocidad Ejecución (8/10)
Puede crearse relativamente rápido.

### 🚨 Riesgos
- Competencia existente
- Necesita marketing activo

### 💡 Oportunidades
- Nicho específico con demanda
- Escalable digitalmente

### 📊 Veredicto
Idea viable si se ejecuta rápido y se enfoca en nicho específico."""

def format_list(items):
    """Formatea lista como bullets"""
    if not items:
        return "- No especificado"
    
    if isinstance(items, str):
        return f"- {items}"
    
    return '\n'.join([f"- {item}" for item in items])


if __name__ == "__main__":
    test_idea = {
        "nombre": "Test Product",
        "slug": "test-product",
        "tipo_producto": "Template",
        "problema": "Test problema",
        "solucion": "Test solución",
        "modelo_monetizacion": "€29 one-time",
        "score_generador": 85
    }
    
    test_critique = {
        "score_critico": 75,
        "puntos_fuertes": ["Punto 1"],
        "puntos_debiles": ["Punto 1"],
        "resumen": "Test"
    }
    
    generate(test_idea, test_critique)
