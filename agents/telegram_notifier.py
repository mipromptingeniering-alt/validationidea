import os
import requests

def send_telegram_notification(idea, critique, landing_url, report_url):
    """Enviar notificación rica a Telegram cuando se publica idea"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    if not bot_token or not chat_id:
        print("⚠️ Variables TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configuradas")
        return False
    
    nombre = idea.get('nombre', 'Nueva Idea')
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    score_promedio = (score_gen + score_crit) / 2
    
    if score_promedio >= 80:
        viabilidad = "ALTA ⭐⭐⭐"
        emoji = "🔥"
    elif score_promedio >= 70:
        viabilidad = "MEDIA ⭐⭐"
        emoji = "💡"
    else:
        viabilidad = "BAJA ⭐"
        emoji = "⚠️"
    
    mercado = idea.get('mercado_objetivo', 'Mercado general')
    tiempo = idea.get('tiempo_estimado', '4-6 semanas')
    monetizacion = idea.get('monetizacion', 'Freemium')
    
    precio_estimado = "€19-29/mes"
    if '$29' in monetizacion or '€29' in monetizacion or '29' in monetizacion:
        precio_estimado = "€29/mes"
        ingreso_anual = "€2,175-4,350"
    elif '$19' in monetizacion or '€19' in monetizacion or '19' in monetizacion:
        precio_estimado = "€19/mes"
        ingreso_anual = "€1,425-2,850"
    elif '$49' in monetizacion or '€49' in monetizacion or '49' in monetizacion:
        precio_estimado = "€49/mes"
        ingreso_anual = "€3,675-7,350"
    else:
        ingreso_anual = "€1,500-3,000"
    
  pages_url = "https://mipromptingeniering-alt.github.io/validationidea"
repo_url = "https://github.com/mipromptingeniering-alt/validationidea/blob/main"
landing_full = f"{pages_url}/{landing_url}"
report_full = f"{repo_url}/{report_url}"

    
    message = f"""🚀 **NUEVA IDEA PUBLICADA**

{emoji} **{nombre}**

📊 **Evaluación:**
• Score Generador: {score_gen}/100
• Score Crítico: {score_crit}/100
• **Promedio: {score_promedio:.1f}/100**
• Viabilidad: {viabilidad}

🎯 **Detalles:**
• Mercado: {mercado}
• Tiempo desarrollo: {tiempo}
• Pricing: {precio_estimado}
• Potencial año 1: {ingreso_anual}

🔗 **Links:**
• 🌐 [Landing Page Pública]({landing_full})
• 📄 [Informe Completo]({report_full})

💼 **Descripción:**
{idea.get('descripcion_corta', 'Sin descripción')}

⚡ **Acción:** Revisa el informe completo para roadmap de 6 semanas y prompt IA listo para Cursor/v0.dev

---
🤖 Sistema Multi-Agente • Groq AI + GitHub Actions
"""
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Notificación Telegram enviada: {nombre}")
            return True
        else:
            print(f"❌ Error Telegram: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error al enviar Telegram: {e}")
        return False

if __name__ == "__main__":
    test_idea = {
        "nombre": "TestApp Pro",
        "descripcion_corta": "Automatiza todo con IA",
        "mercado_objetivo": "Developers y startups",
        "tiempo_estimado": "4 semanas",
        "monetizacion": "€29/mes",
        "score_generador": 85
    }
    test_critique = {"score_critico": 72}
    send_telegram_notification(test_idea, test_critique, "landing-pages/testapp-pro.html", "reports/testapp-pro.md")
