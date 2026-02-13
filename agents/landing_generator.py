import os
import json
from datetime import datetime
import random

def get_unsplash_image(keyword):
    """Generar URL de imagen de Unsplash según keyword"""
    images_map = {
        'saas': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&q=80',
        'productivity': 'https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1200&q=80',
        'automation': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&q=80',
        'marketing': 'https://images.unsplash.com/photo-1557838923-2985c318be48?w=1200&q=80',
        'analytics': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&q=80',
        'design': 'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=1200&q=80',
        'code': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200&q=80',
        'team': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200&q=80',
        'business': 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=1200&q=80',
        'startup': 'https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=1200&q=80'
    }
    keyword_lower = keyword.lower()
    for key in images_map:
        if key in keyword_lower:
            return images_map[key]
    return images_map['saas']

def generate_marketing_landing(idea, critique):
    """Generar landing page optimizada para conversión"""
    nombre = idea.get('nombre', 'Nueva Idea')
    slug = nombre.lower().replace(' ', '-').replace('/', '-')[:30]
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    os.makedirs('landing-pages', exist_ok=True)
    html_file = f'landing-pages/{slug}.html'
    problema = idea.get('problema', 'Un problema común que enfrentan muchos')
    solucion = idea.get('solucion', 'Una solución innovadora')
    propuesta_valor = idea.get('propuesta_valor', 'Ahorra tiempo y dinero')
    mercado = idea.get('mercado_objetivo', 'profesionales')
    descripcion_corta = idea.get('descripcion_corta', '')
    hero_image = get_unsplash_image(nombre + ' ' + mercado)
    interested_count = random.randint(87, 247)
    beta_slots = 50
    countdown_minutes = random.randint(15, 45)
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nombre} - {descripcion_corta[:60]}</title>
    <meta name="description" content="{descripcion_corta}">
    <meta property="og:title" content="{nombre} - Próximamente">
    <meta property="og:description" content="{descripcion_corta}">
    <meta property="og:image" content="{hero_image}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{nombre}">
    <meta name="twitter:description" content="{descripcion_corta}">
    <meta name="twitter:image" content="{hero_image}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #1a202c;
            overflow-x: hidden;
        }}
        .hero {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('{hero_image}') center/cover;
            opacity: 0.15;
            z-index: 0;
        }}
        .hero-content {{ position: relative; z-index: 1; max-width: 900px; margin: 0 auto; }}
        .hero h1 {{ 
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            line-height: 1.2;
            text-shadow: 0 2px 20px rgba(0,0,0,0.2);
        }}
        .hero p {{ 
            font-size: 1.4rem;
            margin-bottom: 40px;
            opacity: 0.95;
            max-width: 700px;
            margin-left: auto;
            margin-right: auto;
        }}
        .countdown-banner {{
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 12px 20px;
            text-align: center;
            font-weight: 600;
            font-size: 0.95rem;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .countdown-timer {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            margin-left: 10px;
            font-weight: 700;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 80px 20px; }}
        .section {{ margin-bottom: 80px; }}
        .section h2 {{ 
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 50px;
            color: #2d3748;
            font-weight: 700;
        }}
        .problem-solution {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-bottom: 60px;
        }}
        .problem, .solution {{
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .problem {{
            background: linear-gradient(135deg, #fef5e7 0%, #fdebd0 100%);
            border-left: 5px solid #f39c12;
        }}
        .solution {{
            background: linear-gradient(135deg, #e8f8f5 0%, #d1f2eb 100%);
            border-left: 5px solid #27ae60;
        }}
        .problem h3, .solution h3 {{
            font-size: 1.5rem;
            margin-bottom: 15px;
            font-weight: 700;
        }}
        .how-it-works {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
            margin-top: 50px;
        }}
        .step {{
            text-align: center;
            padding: 30px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s;
        }}
        .step:hover {{ transform: translateY(-5px); }}
        .step-number {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0 auto 20px;
        }}
        .cta-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 80px 20px;
            text-align: center;
            color: white;
            margin: 0 -20px;
        }}
        .email-form {{
            max-width: 600px;
            margin: 40px auto 0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .email-input {{
            flex: 1;
            min-width: 280px;
            padding: 18px 25px;
            font-size: 1.1rem;
            border: none;
            border-radius: 50px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .submit-btn {{
            padding: 18px 45px;
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }}
        .submit-btn:hover {{ transform: scale(1.05); }}
        .social-proof {{
            text-align: center;
            margin-top: 30px;
            font-size: 0.95rem;
            opacity: 0.9;
        }}
        .trust-badges {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 40px;
            flex-wrap: wrap;
        }}
        .badge {{
            background: rgba(255,255,255,0.15);
            padding: 12px 25px;
            border-radius: 30px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        .faq {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .faq-item {{
            background: white;
            padding: 25px;
            margin-bottom: 15px;
            border-radius: 12px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        }}
        .faq-question {{
            font-weight: 700;
            font-size: 1.15rem;
            margin-bottom: 10px;
            color: #2d3748;
        }}
        .faq-answer {{ color: #4a5568; line-height: 1.7; }}
        .scarcity-box {{
            background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
            border: 2px dashed #fc8181;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin: 40px auto;
            max-width: 600px;
        }}
        .scarcity-box strong {{ color: #c53030; font-size: 1.2rem; }}
        #exit-popup {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        .popup-content {{
            background: white;
            padding: 50px;
            border-radius: 20px;
            max-width: 500px;
            text-align: center;
            position: relative;
        }}
        .popup-close {{
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 2rem;
            cursor: pointer;
            color: #999;
        }}
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2.2rem; }}
            .hero p {{ font-size: 1.1rem; }}
            .problem-solution {{ grid-template-columns: 1fr; }}
            .how-it-works {{ grid-template-columns: 1fr; }}
            .email-form {{ flex-direction: column; }}
            .email-input, .submit-btn {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="countdown-banner">
        ⚡ Oferta especial de lanzamiento: Sé de los primeros {beta_slots} beta testers
        <span class="countdown-timer" id="countdown">{countdown_minutes}:00</span>
    </div>

    <section class="hero">
        <div class="hero-content">
            <h1>{nombre}</h1>
            <p>{descripcion_corta}</p>
            <form class="email-form" onsubmit="handleSubmit(event)">
                <input type="email" class="email-input" placeholder="Tu mejor email" required>
                <button type="submit" class="submit-btn">Quiero acceso anticipado 🚀</button>
            </form>
            <div class="social-proof">
                ✅ {interested_count} personas ya se unieron • 🔒 Sin spam, lo prometemos
            </div>
        </div>
    </section>

    <div class="container">
        <section class="section">
            <h2>El Problema que Resolvemos</h2>
            <div class="problem-solution">
                <div class="problem">
                    <h3>😤 Antes (El problema)</h3>
                    <p>{problema}</p>
                </div>
                <div class="solution">
                    <h3>✨ Después (Con {nombre})</h3>
                    <p>{solucion}</p>
                </div>
            </div>
        </section>

        <section class="section">
            <h2>Cómo Funciona</h2>
            <div class="how-it-works">
                <div class="step">
                    <div class="step-number">1</div>
                    <h3>Regístrate gratis</h3>
                    <p>Crea tu cuenta en menos de 2 minutos. Sin tarjeta de crédito.</p>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <h3>Configura en 1 clic</h3>
                    <p>Setup automático guiado. Empieza a usar en segundos.</p>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <h3>Ve resultados inmediatos</h3>
                    <p>Ahorra tiempo desde el primer día. Sin curva de aprendizaje.</p>
                </div>
            </div>
        </section>

        <div class="scarcity-box">
            <strong>⚠️ Solo {beta_slots} plazas disponibles</strong>
            <p>Los primeros beta testers obtendrán acceso lifetime gratuito + influencia directa en el roadmap del producto.</p>
        </div>

        <section class="cta-section">
            <h2>¿Listo para Transformar tu {mercado.split()[0] if mercado else 'Trabajo'}?</h2>
            <p style="font-size: 1.2rem; margin-bottom: 30px;">{propuesta_valor}</p>
            <form class="email-form" onsubmit="handleSubmit(event)">
                <input type="email" class="email-input" placeholder="tu@email.com" required>
                <button type="submit" class="submit-btn">Unirme ahora gratis</button>
            </form>
            <div class="trust-badges">
                <div class="badge">✅ Gratis para siempre</div>
                <div class="badge">🔒 Datos seguros</div>
                <div class="badge">⚡ Setup en 2 minutos</div>
                <div class="badge">💬 Soporte prioritario</div>
            </div>
        </section>

        <section class="section">
            <h2>Preguntas Frecuentes</h2>
            <div class="faq">
                <div class="faq-item">
                    <div class="faq-question">¿Cuándo estará disponible?</div>
                    <div class="faq-answer">Estamos en fase beta privada. Los registrados en lista de espera tendrán acceso en las próximas 2-4 semanas.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">¿Es realmente gratis?</div>
                    <div class="faq-answer">Sí. Los primeros {beta_slots} beta testers tendrán acceso lifetime gratuito al plan completo como agradecimiento por su feedback temprano.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">¿Necesito conocimientos técnicos?</div>
                    <div class="faq-answer">Para nada. {nombre} está diseñado para ser usado por cualquier persona sin conocimientos técnicos.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">¿Qué pasa con mis datos?</div>
                    <div class="faq-answer">Tus datos están encriptados y seguros. Nunca compartimos información con terceros. GDPR compliant.</div>
                </div>
            </div>
        </section>
    </div>

    <div id="exit-popup">
        <div class="popup-content">
            <span class="popup-close" onclick="closePopup()">&times;</span>
            <h2 style="margin-bottom: 20px;">✋ ¡Espera!</h2>
            <p style="margin-bottom: 30px;">No pierdas tu lugar en la lista de espera. Los primeros {beta_slots} obtienen acceso lifetime gratuito.</p>
            <form class="email-form" onsubmit="handleSubmit(event)">
                <input type="email" class="email-input" placeholder="Tu email" required>
                <button type="submit" class="submit-btn">Asegurar mi lugar</button>
            </form>
        </div>
    </div>

    <script>
        let countdownMinutes = {countdown_minutes};
        let countdownSeconds = 0;
        
        function updateCountdown() {{
            const display = document.getElementById('countdown');
            if (countdownSeconds === 0) {{
                if (countdownMinutes === 0) {{
                    display.textContent = '¡Oferta terminada!';
                    return;
                }}
                countdownMinutes--;
                countdownSeconds = 59;
            }} else {{
                countdownSeconds--;
            }}
            const mins = String(countdownMinutes).padStart(2, '0');
            const secs = String(countdownSeconds).padStart(2, '0');
            display.textContent = mins + ':' + secs;
        }}
        
        setInterval(updateCountdown, 1000);
        
        let exitIntentShown = false;
        document.addEventListener('mouseleave', (e) => {{
            if (e.clientY <= 0 && !exitIntentShown) {{
                document.getElementById('exit-popup').style.display = 'flex';
                exitIntentShown = true;
            }}
        }});
        
        function closePopup() {{
            document.getElementById('exit-popup').style.display = 'none';
        }}
        
        function handleSubmit(e) {{
            e.preventDefault();
            const email = e.target.querySelector('input[type="email"]').value;
            alert('¡Gracias! Te contactaremos pronto a: ' + email);
            closePopup();
            localStorage.setItem('email_submitted', email);
        }}
    </script>
</body>
</html>
"""
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Landing page marketing creada: {html_file}")
    return slug

if __name__ == "__main__":
    test_idea = {"nombre": "AutoTask Pro", "descripcion_corta": "Automatiza tus tareas repetitivas y ahorra 10 horas semanales", "problema": "Pierdes horas cada semana en tareas manuales repetitivas que te quitan tiempo para lo importante", "solucion": "Automatiza todo con 1 clic. Sin código, sin complicaciones", "propuesta_valor": "Recupera 10+ horas cada semana", "mercado_objetivo": "Freelancers y pequeños equipos"}
    test_critique = {"score_critico": 70}
    generate_marketing_landing(test_idea, test_critique)
