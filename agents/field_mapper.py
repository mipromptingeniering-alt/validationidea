"""
Field Mapper - Mapea campos de generator_agent a notion_sync_agent
"""

def map_idea_fields(raw_idea):
    """
    Convierte campos de generator_agent al formato que Notion espera
    """
    
    # Construir MVP desde varios campos
    mvp_parts = []
    if raw_idea.get('stack_sugerido'):
        mvp_parts.append(f"Stack: {raw_idea['stack_sugerido']}")
    if raw_idea.get('features_core'):
        mvp_parts.append(f"Features: {raw_idea['features_core']}")
    if raw_idea.get('tiempo_estimado'):
        mvp_parts.append(f"Tiempo: {raw_idea['tiempo_estimado']}")
    if raw_idea.get('roadmap_mvp'):
        mvp_parts.append(f"Roadmap: {raw_idea['roadmap_mvp']}")
    
    mvp_text = '. '.join(mvp_parts) if mvp_parts else 'Por definir'
    
    # Construir modelo de negocio
    negocio_parts = []
    if raw_idea.get('modelo_monetizacion'):
        negocio_parts.append(raw_idea['modelo_monetizacion'])
    if raw_idea.get('precio_sugerido'):
        negocio_parts.append(f"Precio: €{raw_idea['precio_sugerido']}")
    if raw_idea.get('como_monetizar'):
        negocio_parts.append(f"Cómo: {raw_idea['como_monetizar']}")
    
    modelo_negocio = '. '.join(negocio_parts) if negocio_parts else 'Por definir'
    
    # Mapear campos
    mapped = {
        # Crítica (mapear puntos_fuertes/debiles a fortalezas/debilidades)
        'fortalezas': raw_idea.get('puntos_fuertes', []),
        'fortalezas': raw_idea.get('puntos_fuertes', []),
        'debilidades': raw_idea.get('puntos_debiles', []),
        'puntos_fuertes': raw_idea.get('puntos_fuertes', []),
        'puntos_debiles': raw_idea.get('puntos_debiles', []),
        # Básicos
        'nombre': raw_idea.get('nombre', 'Sin nombre'),
        'titulo': raw_idea.get('nombre', 'Sin nombre'),
        'descripcion': raw_idea.get('descripcion', ''),
        'problema': raw_idea.get('problema', ''),
        'solucion': raw_idea.get('solucion', ''),
        
        # Target
        'publico_objetivo': raw_idea.get('publico_objetivo', ''),
        'target': raw_idea.get('publico_objetivo', ''),
        
        # Business y MVP (construidos)
        'modelo_negocio': modelo_negocio,
        'mvp': mvp_text,
        
        # Valor
        'propuesta_valor': raw_idea.get('propuesta_valor', ''),
        
        # Métricas
        'metricas_clave': raw_idea.get('metricas_clave', 'MRR, CAC, LTV'),
        'metricas': raw_idea.get('metricas_clave', 'MRR, CAC, LTV'),
        
        # Riesgos
        'riesgos': raw_idea.get('riesgos', 'Por definir'),
        
        # Marketing (desde canales_adquisicion)
        'canales_marketing': raw_idea.get('canales_adquisicion', ''),
        'estrategia_marketing': raw_idea.get('canales_adquisicion', ''),
        
        # Próximos pasos (desde roadmap o validacion_inicial)
        'proximos_pasos': raw_idea.get('roadmap_mvp', '') or 
                         f"1. {raw_idea.get('validacion_inicial', 'Validar con clientes')}. " +
                         f"2. Construir MVP ({raw_idea.get('tiempo_estimado', '2-4 semanas')}). " +
                         "3. Lanzar y obtener feedback.",
        
        # Scores
        'score_generador': raw_idea.get('score_generador', 75),
        'score_critico': raw_idea.get('score_critico', 0),
        'score_viral': raw_idea.get('viral_score', 0),
        'viral_score': raw_idea.get('viral_score', 0),
        
        # Metadata (preservar todo lo demás)
        'fecha': raw_idea.get('created_at', raw_idea.get('fecha')),
        '_fingerprint': raw_idea.get('_fingerprint', ''),
        'research': raw_idea.get('research', {}),
        'research_summary': str(raw_idea.get('research', {}).get('diferenciacion_clave', '')),
        'critique': raw_idea.get('critique', {}),
        
        # Preservar campos originales por si acaso
        **{k: v for k, v in raw_idea.items() if k not in [
            'nombre', 'descripcion', 'problema', 'solucion', 'publico_objetivo',
            'propuesta_valor', 'metricas_clave', 'riesgos', 'canales_adquisicion',
            'roadmap_mvp', 'validacion_inicial', 'score_generador', 'score_critico',
            'viral_score', 'created_at', 'fecha', '_fingerprint', 'research', 'critique'
        ]}
    }
    
    return mapped

if __name__ == '__main__':
    # Test
    test_idea = {
        'nombre': 'Test Product',
        'problema': 'Problema test',
        'stack_sugerido': 'Notion, Gumroad',
        'features_core': 'Feature 1, Feature 2',
        'tiempo_estimado': '2 semanas',
        'roadmap_mvp': 'Fase 1 → Fase 2 → Lanzamiento',
        'precio_sugerido': '29',
        'como_monetizar': 'Vender en Gumroad'
    }
    
    mapped = map_idea_fields(test_idea)
    import json
    print(json.dumps(mapped, indent=2, ensure_ascii=False))



