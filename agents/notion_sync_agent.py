"""
Notion Sync Agent - Sincronización de ideas a Notion
CORREGIDO: Encoding UTF-8 + mapeo correcto de campos
"""
import os
import json
from datetime import datetime
from notion_client import Client

def sync_idea_to_notion(idea):
    """
    Sincroniza idea a Notion con encoding correcto
    """
    try:
        notion = Client(auth=os.environ.get("NOTION_TOKEN"))
        database_id = "308313aca133800981cfc48f32c52146"
        
        # Preparar propiedades con encoding correcto
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": str(idea.get('titulo', idea.get('nombre', 'Sin título')))[:2000]
                        }
                    }
                ]
            },
            "Description": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('descripcion', ''))[:2000]
                        }
                    }
                ]
            },
            "Problem": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('problema', ''))[:2000]
                        }
                    }
                ]
            },
            "Solution": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('solucion', ''))[:2000]
                        }
                    }
                ]
            },
            "Target": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('target', idea.get('publico_objetivo', '')))[:2000]
                        }
                    }
                ]
            },
            "Business": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('modelo_negocio', ''))[:2000]
                        }
                    }
                ]
            },
            "MVP": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('mvp', ''))[:2000]
                        }
                    }
                ]
            },
            "Value": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('propuesta_valor', ''))[:2000]
                        }
                    }
                ]
            },
            "Metrics": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('metricas', ''))[:2000]
                        }
                    }
                ]
            },
            "Risks": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('riesgos', ''))[:2000]
                        }
                    }
                ]
            },
            "Marketing": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('estrategia_marketing', ''))[:2000]
                        }
                    }
                ]
            },
            "Monetization": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(idea.get('monetizacion', ''))[:2000]
                        }
                    }
                ]
            },
            "Scoring": {
                "rich_text": [
                    {
                        "text": {
                            "content": f"Score Crítico: {idea.get('score_critico', 0)}/100\nScore Viral: {idea.get('score_viral', 0)}/100\nScore Total: {idea.get('score_total', 0)}/100"
                        }
                    }
                ]
            },
            "ScoreFinal": {
                "number": int(idea.get('score_total', idea.get('score_critico', 0)))
            }
        }
        
        # Crear página en Notion
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        
        print(f"✅ Sincronizado a Notion: {page['url']}")
        return page
        
    except Exception as e:
        print(f"❌ Error Notion: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test
    test_idea = {
        "titulo": "Test Idea con Ácentós y Émojis 🚀",
        "nombre": "TestProduct",
        "descripcion": "Descripción de prueba con ñ y tildes",
        "problema": "Problema a resolver",
        "score_critico": 85,
        "score_total": 85
    }
    
    sync_idea_to_notion(test_idea)
