import os
import json
from datetime import datetime
import sys

def process_order(customer_name, customer_email, idea_data):
    """Procesa pedido de validación"""
    
    print(f"\n🎯 Procesando validación para: {customer_name}\n")
    
    # 1. Guardar datos cliente
    order_id = f"VAL-{datetime.now().strftime('%Y%m%d-%H%M')}"
    
    order_data = {
        "order_id": order_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "idea": idea_data,
        "created_at": datetime.now().isoformat(),
        "status": "processing"
    }
    
    os.makedirs('orders', exist_ok=True)
    
    with open(f'orders/{order_id}.json', 'w') as f:
        json.dump(order_data, f, indent=2)
    
    print(f"✅ Pedido guardado: {order_id}")
    
    # 2. Crear idea para el sistema
    idea_for_system = {
        "nombre": idea_data.get('nombre', 'Idea Cliente'),
        "slug": f"client-{order_id.lower()}",
        "problema": idea_data.get('problema'),
        "solucion": idea_data.get('solucion'),
        "publico_objetivo": idea_data.get('target', 'No especificado'),
        "descripcion_corta": idea_data.get('problema', '')[:100],
        "score_generador": 90  # Cliente pagó, alta prioridad
    }
    
    print(f"✅ Idea preparada para análisis\n")
    
    # 3. Instrucciones para ti
    print("📋 SIGUIENTE PASO:")
    print(f"   1. Ejecuta: python main_workflow.py (generará análisis automático)")
    print(f"   2. Revisa informe en: informes/{idea_for_system['slug']}/")
    print(f"   3. Añade tu análisis manual (30 min)")
    print(f"   4. Envía a: {customer_email}")
    print(f"   5. Marca completado: python scripts/mark-complete.py {order_id}")
    
    return order_id


if __name__ == "__main__":
    # Ejemplo uso
    if len(sys.argv) > 1:
        order_id = sys.argv[1]
        print(f"Procesando pedido: {order_id}")
    else:
        # Test
        test_data = {
            "nombre": "Test Validation",
            "problema": "Freelancers no saben qué precio cobrar",
            "solucion": "Calculator que analiza mercado y sugiere pricing",
            "target": "Freelancers tech"
        }
        
        process_order(
            "Test Customer",
            "test@example.com",
            test_data
        )
