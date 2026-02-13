import os
import json
from datetime import datetime

def generate_report(idea, critique):
    """
    Generar informe completo en Markdown.
    Análisis pragmático, sin paja, con números realistas.
    """
    
    nombre = idea.get('nombre', 'Idea sin nombre')
    slug = nombre.lower().replace(' ', '-').replace('/', '-')[:30]
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    
    os.makedirs('reports', exist_ok=True)
    report_file = f'reports/{slug}.md'
    
    # Calcular métricas realistas
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    score_promedio = (score_gen + score_crit) / 2
    
    # Evaluación de viabilidad
    if score_promedio >= 80:
        viabilidad = "ALTA ⭐⭐⭐"
        recomendacion = "Idea sólida con alto potencial. Vale la pena ejecutar."
    elif score_promedio >= 70:
        viabilidad = "MEDIA ⭐⭐"
        recomendacion = "Idea viable con riesgos manejables. Validar antes de invertir mucho tiempo."
    else:
        viabilidad = "BAJA ⭐"
        recomendacion = "Idea con riesgos significativos. Solo ejecutar si tienes ventaja única."
    
    # Estimación TAM/SAM realista
    tam_estimado = estimar_mercado(idea.get('mercado_objetivo', ''))
    
    # Tech stack con enlaces
    tech_stack_links = generar_tech_stack_links(idea.get('tech_stack', []))
    
    # Roadmap realista
    roadmap = generar_roadmap(idea.get('tiempo_estimado', '4 semanas'))
    
    # Prompt JSON para IA
    prompt_json = generar_prompt_json(idea)
    
    # Generar informe
    report_content = f"""# 📊 Informe Completo: {nombre}

**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Viabilidad:** {viabilidad}  
**Score Generador:** {score_gen}/100 | **Score Crítico:** {score_crit}/100

---

## 🎯 Resumen Ejecutivo

{idea.get('descripcion_corta', '')}

**Problema:** {idea.get('problema', '')}

**Solución:** {idea.get('solucion', '')}

---

## 💡 Propuesta de Valor

{idea.get('propuesta_valor', '')}

**Diferenciación clave:** {idea.get('diferenciacion', '')}

---

## 👥 Mercado Objetivo

**Target:** {idea.get('mercado_objetivo', '')}

### Análisis de Mercado (TAM/SAM/SOM)

{tam_estimado}

---

## 🏢 Competencia

"""
    
    competencia = idea.get('competencia', [])
    for comp in competencia:
        report_content += f"- **{comp}**\n"
    
    report_content += f"""
### Análisis Competitivo

**Fortalezas de tu idea:**
"""
    
    fortalezas = critique.get('fortalezas', [])
    for f in fortalezas:
        report_content += f"- {f}\n"
    
    report_content += f"""
**Debilidades identificadas:**
"""
    
    debilidades = critique.get('debilidades', [])
    for d in debilidades:
        report_content += f"- {d}\n"
    
    report_content += f"""
---

## 💰 Modelo de Negocio

{idea.get('monetizacion', '')}

### Proyección Realista (Año 1)

- **Mes 1-2:** Desarrollo MVP + primeros 10 beta testers (€0)
- **Mes 3:** Lanzamiento público. Meta: 50 usuarios (5 pagando) → €{calcular_ingreso_mes3(idea)}
- **Mes 6:** Crecimiento orgánico. Meta: 200 usuarios (25 pagando) → €{calcular_ingreso_mes6(idea)}
- **Mes 12:** Escala. Meta: 500 usuarios (75 pagando) → €{calcular_ingreso_mes12(idea)}

**Inversión inicial:** €0-500 (dominio + hosting año 1)  
**Break-even esperado:** Mes 4-6

---

## 🛠️ Stack Tecnológico 2026

{tech_stack_links}

**Justificación:**
- Rápido desarrollo (MVP en {idea.get('tiempo_estimado', '4 semanas')})
- Costo €0/mes hasta primeros clientes
- Escalable sin reescribir
- Modern DX (Developer Experience)

---

## 📅 Roadmap Realista

{roadmap}

---

## 🚨 Riesgos y Mitigación

"""
    
    riesgos = critique.get('riesgos_mayores', [])
    for i, riesgo in enumerate(riesgos, 1):
        report_content += f"""
### Riesgo #{i}: {riesgo}

**Mitigación:** Validar con 10 usuarios objetivo antes de invertir más de 40h.
"""
    
    report_content += f"""
---

## 🎯 Opinión Profesional (Análisis Pragmático)

**Veredicto del Crítico:**  
{critique.get('veredicto_honesto', 'No disponible')}

**Probabilidad de éxito:** {critique.get('probabilidad_exito', 'N/A')}

### Mi Evaluación

**¿Vale la pena ejecutar?** {recomendacion}

**Factores críticos de éxito:**
1. Validar problema con 10 conversaciones reales (antes de escribir código)
2. MVP super simple: 1 funcionalidad core, bien hecha
3. Go-to-market: encontrar el canal donde están tus usuarios (no "redes sociales")
4. Pricing: empezar caro ($29/mes mejor que $9/mes para validar)

**Red flags a vigilar:**
- Si nadie paga después de 50 conversaciones → pivotar o abandonar
- Si competencia grande lanza feature similar → acelerar diferenciación
- Si churn >10% mensual → problema de product-market fit

---

## 🤖 Prompt para Desarrollar con IA (Cursor, v0.dev, Bolt)

Usa este JSON con Cursor AI / v0.dev / Bolt.new:

```json
{prompt_json}
