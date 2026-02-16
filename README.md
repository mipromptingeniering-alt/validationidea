# 🚀 CHET THIS v2.0 - Sistema Auto-Evolutivo de Validación de Ideas

Sistema inteligente que **aprende automáticamente** de cada idea generada, optimiza sus prompts y mejora continuamente.

## 🧬 Características Auto-Evolutivas

### 1. Memoria Persistente
- ✅ Analiza cada idea generada
- ✅ Detecta patrones de éxito/fracaso
- ✅ Aprende qué funciona y qué no

### 2. Auto-Refinamiento de Prompts
- ✅ Optimiza prompts basándose en resultados
- ✅ Ajusta temperatura según tasa de éxito
- ✅ Incorpora keywords exitosos automáticamente

### 3. Research Inteligente
- ✅ Valida mercado y competencia
- ✅ Detecta oportunidades específicas
- ✅ Genera recomendaciones accionables

### 4. Sincronización Automática
- ✅ Notion: Base de datos completa
- ✅ Telegram: Notificaciones instant
- ✅ GitHub Actions: Ejecución cada 15 min

## 📊 Estado Actual

\\\ash
# Ver dashboard de evolución
python dashboard.py

# Generar idea manualmente
python run_batch.py

# Test completo
python -m pytest tests/
\\\

## 🔄 Flujo Automático

1. **Cada 15 minutos** (GitHub Actions):
   - Genera 1 idea usando prompts optimizados
   - Analiza con sistema evolutivo
   - Actualiza knowledge base
   - Sincroniza a Notion
   - Envía notificación a Telegram

2. **Sistema aprende**:
   - Detecta qué categorías tienen mejor score
   - Identifica keywords exitosos
   - Ajusta temperatura de generación
   - Refina diferenciación automáticamente

## 📁 Estructura

\\\
validationidea/
├── agents/
│   ├── generator_agent.py      # Generación con prompts optimizados
│   ├── knowledge_base.py       # Memoria persistente
│   ├── prompt_optimizer.py     # Auto-refinamiento
│   ├── researcher_agent.py     # Validación inteligente
│   ├── critic_agent.py         # Evaluación
│   ├── notion_sync_agent.py    # Sincronización
│   └── field_mapper.py         # Mapeo de campos
├── data/
│   ├── ideas.json              # Ideas generadas
│   ├── knowledge_base.json     # Aprendizajes
│   └── prompt_evolution.json   # Evolución de prompts
├── .github/workflows/
│   └── auto_ideas_15min.yml    # Workflow único
├── dashboard.py                # Visualización
├── run_batch.py                # Orquestador
└── README.md
\\\

## 🎯 Próximas Mejoras

- [ ] Integración con Tavily API para research real
- [ ] A/B testing automático de prompts
- [ ] Clustering de ideas similares
- [ ] Predicción de viabilidad con ML
- [ ] Dashboard web interactivo

## 📈 Métricas

- **Tasa de éxito**: Score promedio de ideas generadas
- **Mejora continua**: % de mejora en últimas 10 ideas
- **Patrones detectados**: Keywords, categorías, stacks exitosos
- **Evolución de prompts**: Versiones y mejora acumulada

---

**Desarrollado con ❤️ por el sistema que se mejora a sí mismo**
