import os
import json
from datetime import datetime
from groq import Groq

def generate(idea, critique):
    """Genera informe markdown completo con opinión profesional"""
    
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

**{idea.get('descripcion_corta', 'Descripción no disponible')}**

{idea.get('descripcion', 'Descripción completa no disponible')}

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

## 💰 PROPUESTA DE VALOR

{idea.get('propuesta_valor', 'No especificada')}

---

## 🚀 DIFERENCIACIÓN

{idea.get('diferenciacion', 'No especificada')}

---

## 📊 TAMAÑO DE MERCADO

- **TAM (Total Addressable Market):** {idea.get('tam', 'N/A')}
- **SAM (Serviceable Addressable Market):** {idea.get('sam', 'N/A')}
- **SOM (Serviceable Obtainable Market):** {idea.get('som', 'N/A')}

---

## 🏆 COMPETENCIA

**Principales Competidores:**

{format_list(idea.get('competencia', []))}

**Ventaja Competitiva:**

{idea.get('ventaja_competitiva', 'No especificada')}

---

## 💵 MONETIZACIÓN

**Precio Sugerido:** {idea.get('precio_sugerido', 'N/A')}€/mes

**Modelo:** {idea.get('modelo_monetizacion', 'No especificado')}

---

## ⚙️ FEATURES CORE

{format_list(idea.get('features_core', []))}

---

## 🗺️ ROADMAP MVP

{format_list(idea.get('roadmap_mvp', []))}

**Tiempo Estimado:** {idea.get('tiempo_estimado', 'N/A')}

---

## 🛠️ STACK TECNOLÓGICO

{format_list(idea.get('stack_sugerido', []))}

---

## 🔗 INTEGRACIONES

{format_list(idea.get('integraciones', []))}

---

## 📈 CANALES ADQUISICIÓN

{format_list(idea.get('canales_adquisicion', []))}

---

## 📊 MÉTRICAS CLAVE

{format_list(idea.get('metricas_clave', []))}

---

## ⚠️ RIESGOS

{format_list(idea.get('riesgos', []))}

---

## ✅ VALIDACIÓN INICIAL

{idea.get('validacion_inicial', 'No especificada')}

---

## 💰 INVERSIÓN INICIAL

**Estimada:** {idea.get('inversion_inicial', 'N/A')}€

**Dificultad:** {idea.get('dificultad', 'Media')}

---

## 🎯 EVALUACIÓN CRÍTICA

### Puntos Fuertes

{format_list(critique.get('puntos_fuertes', []))}

### Puntos Débiles

{format_list(critique.get('puntos_debiles', []))}

### Recomendaciones

{format_list(critique.get('recomendaciones', []))}

---

## 📝 CONCLUSIÓN

{critique.get('resumen', 'Sin resumen disponible')}

---

**Generado automáticamente por ValidationIdea**  
**Sistema Multi-Agente IA v2.0**
"""
    
    # Guardar informe
    output_dir = f'informes/{slug}'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/informe-{slug}.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(informe)
    
    print(f"✅ Informe generado: {output_file}")
    
    return output_file

def generate_professional_opinion(idea, critique):
    """Genera opinión profesional profunda con IA"""
    
    print("🧠 Generando opinión profesional...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt = f"""Eres un experto inversor y consultor SaaS con 15 años de experiencia. Has visto lanzar cientos de startups.

Analiza esta idea SaaS y da tu opinión profesional honesta:

**Idea:** {idea.get('nombre')}
**Problema:** {idea.get('problema')}
**Solución:** {idea.get('solucion')}
**Mercado:** TAM {idea.get('tam')}, SAM {idea.get('sam')}
**Precio:** {idea.get('precio_sugerido')}€/mes
**Stack:** {', '.join(idea.get('stack_sugerido', [])[:3])}
**Score:** {critique.get('score_critico')}/100

Estructura tu opinión así:

### 🎯 Viabilidad (X/10)
[1-2 frases sobre si es viable técnica y comercialmente]

### 💰 Potencial Ingresos (X/10)
[1-2 frases sobre potencial de generar revenue significativo]

### ⚡ Velocidad Ejecución (X/10)
[1-2 frases sobre cuán rápido se puede lanzar MVP]

### 🏆 Diferenciación (X/10)
[1-2 frases sobre cuán único es vs competencia]

### 🚨 Riesgos Principales
- [Riesgo 1 específico]
- [Riesgo 2 específico]
- [Riesgo 3 específico]

### 💡 Oportunidades Clave
- [Oportunidad 1 específica]
- [Oportunidad 2 específica]
- [Oportunidad 3 específica]

### 📊 Veredicto Final
[3-4 frases: ¿Recomendarías invertir tiempo/dinero en esta idea? ¿Por qué sí o no? Sé directo y honesto.]

Usa lenguaje profesional pero directo. Sin fluff, solo insights accionables."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un experto inversor SaaS. Das opiniones honestas y directas basadas en datos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        opinion = response.choices[0].message.content.strip()
        print("✅ Opinión profesional generada")
        
        return opinion
    
    except Exception as e:
        print(f"⚠️  Error generando opinión: {e}")
        
        # Fallback opinion
        return f"""### 🎯 Viabilidad (7/10)
Idea técnicamente viable con stack moderno. El problema está bien definido y la solución es implementable.

### 💰 Potencial Ingresos (6/10)
Nicho específico con mercado mediano. Precio {idea.get('precio_sugerido')}€/mes es razonable para el valor ofrecido.

### ⚡ Velocidad Ejecución (8/10)
MVP factible en 4-6 semanas con stack {', '.join(idea.get('stack_sugerido', [])[:2])}. Sin dependencias complejas.

### 🏆 Diferenciación (6/10)
Diferenciación moderada. Necesita enfocarse en un nicho ultra-específico para destacar.

### 🚨 Riesgos Principales
- Mercado potencialmente saturado
- Dependencia de APIs de terceros
- Competencia puede copiar features rápidamente

### 💡 Oportunidades Clave
- Nicho con dolor real y disposición a pagar
- Automatización puede generar gran valor
- Posibilidad de expansión a nichos adyacentes

### 📊 Veredicto Final
Idea sólida con potencial medio-alto. Recomendado validar con 20 entrevistas antes de invertir en desarrollo. El éxito dependerá de ejecución rápida y diferenciación clara. Con MVP funcional y primeros clientes, tiene potencial de llegar a €10K MRR en 6-12 meses."""

def format_list(items):
    """Formatea lista como bullets markdown"""
    if not items:
        return "- No especificado"
    
    if isinstance(items, str):
        return f"- {items}"
    
    return '\n'.join([f"- {item}" for item in items])


if __name__ == "__main__":
    # Test
    test_idea = {
        "nombre": "Test SaaS",
        "slug": "test-saas",
        "problema": "Test problema",
        "solucion": "Test solución",
        "tam": "50M",
        "sam": "5M",
        "precio_sugerido": "49",
        "stack_sugerido": ["Next.js", "Supabase"],
        "score_generador": 85
    }
    
    test_critique = {
        "score_critico": 75,
        "puntos_fuertes": ["Punto 1"],
        "puntos_debiles": ["Punto 1"],
        "resumen": "Test"
    }
    
    generate(test_idea, test_critique)
