"""
Telegram Agent: notificaciones de nuevas ideas
"""
import os
import requests

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_notification(idea):
    """Envía notificación de nueva idea"""
    
    if not BOT_TOKEN or not CHAT_ID:
        print('⚠️ Telegram no configurado')
        return
    
    # Construir mensaje
    emoji = get_emoji(idea.get('score_critico', 0), idea.get('viral_score', 0))
    
    estimation = idea.get('estimation', {})
    inv = estimation.get('inversion_mvp_usd', 'N/A') if estimation else 'N/A'
    weeks = estimation.get('tiempo_desarrollo_semanas', 'N/A') if estimation else 'N/A'
    
    message = f"""{emoji} **NUEVA IDEA DE CALIDAD**

📝 **{idea.get('nombre', 'Sin nombre')}**

{idea.get('descripcion', 'Sin descripción')[:200]}

📊 **Scores:**
• Crítico: {idea.get('score_critico', 0)}/100
• Viral: {idea.get('viral_score', 0)}/100

💰 **Inversión estimada:** ${inv}
⏱️ **Tiempo:** {weeks} semanas

🔗 [Ver en Notion]({idea.get('notion_url', '#')})
"""
    
    # Enviar
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print('✅ Notificación Telegram enviada')
        else:
            print(f'⚠️ Error Telegram: {response.text}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

def get_emoji(score, viral):
    """Devuelve emoji según scores"""
    if score >= 90:
        return '💎'
    elif score >= 85:
        return '⭐'
    elif viral >= 85:
        return '🔥'
    else:
        return '💡'