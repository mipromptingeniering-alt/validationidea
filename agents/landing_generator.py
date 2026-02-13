import os
from datetime import datetime

def generate_landing(idea_data):
    """
    Genera una landing page HTML completa para capturar emails vía Vercel Function
    """
    
    slug = idea_data.get('slug', 'idea')
    nombre = idea_data.get('nombre', 'Idea SaaS')
    descripcion = idea_data.get('descripcion', 'Una idea innovadora')
    problema = idea_data.get('problema', 'Problema a resolver')
    solucion = idea_data.get('solucion', 'Nuestra solución')
    tam = idea_data.get('tam', 'N/A')
    sam = idea_data.get('sam', 'N/A')
    som = idea_data.get('som', 'N/A')
    precio_sugerido = idea_data.get('precio_sugerido', '29€/mes')
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nombre} - Solución Innovadora</title>
    <meta name="description" content="{descripcion}">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .animate-float {{
            animation: float 3s ease-in-out infinite;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
        }}
    </style>
</head>
<body class="bg-gray-50">
    
    <!-- Hero Section -->
    <section class="gradient-bg text-white py-20 px-4">
        <div class="max-w-4xl mx-auto text-center">
            <h1 class="text-5xl font-bold mb-6 animate-float">{nombre}</h1>
            <p class="text-xl mb-8 opacity-90">{descripcion}</p>
            <div class="bg-white/10 backdrop-blur-md rounded-lg p-6 inline-block">
                <p class="text-2xl font-semibold">🎯 Próximo Lanzamiento</p>
                <p class="text-lg mt-2">Sé de los primeros en probarlo</p>
            </div>
        </div>
    </section>

    <!-- Problema Section -->
    <section class="py-16 px-4 bg-white">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl font-bold text-center mb-8 text-gray-800">❌ El Problema</h2>
            <p class="text-lg text-gray-600 text-center leading-relaxed">{problema}</p>
        </div>
    </section>

    <!-- Solución Section -->
    <section class="py-16 px-4 bg-gray-50">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl font-bold text-center mb-8 text-gray-800">✅ Nuestra Solución</h2>
            <p class="text-lg text-gray-600 text-center leading-relaxed">{solucion}</p>
        </div>
    </section>

    <!-- Mercado Section -->
    <section class="py-16 px-4 bg-white">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl font-bold text-center mb-12 text-gray-800">📊 Oportunidad de Mercado</h2>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="bg-blue-50 p-6 rounded-lg text-center">
                    <p class="text-sm text-blue-600 font-semibold mb-2">TAM (Total)</p>
                    <p class="text-2xl font-bold text-gray-800">{tam}</p>
                </div>
                <div class="bg-purple-50 p-6 rounded-lg text-center">
                    <p class="text-sm text-purple-600 font-semibold mb-2">SAM (Servible)</p>
                    <p class="text-2xl font-bold text-gray-800">{sam}</p>
                </div>
                <div class="bg-pink-50 p-6 rounded-lg text-center">
                    <p class="text-sm text-pink-600 font-semibold mb-2">SOM (Objetivo)</p>
                    <p class="text-2xl font-bold text-gray-800">{som}</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Precio Section -->
    <section class="py-16 px-4 bg-gray-50">
        <div class="max-w-4xl mx-auto text-center">
            <h2 class="text-3xl font-bold mb-8 text-gray-800">💰 Precio Estimado</h2>
            <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-8 rounded-lg inline-block">
                <p class="text-4xl font-bold">{precio_sugerido}</p>
                <p class="text-lg mt-2 opacity-90">Precio de lanzamiento especial</p>
            </div>
        </div>
    </section>

    <!-- CTA Final Section -->
    <section class="py-20 px-4 gradient-bg text-white">
        <div class="max-w-2xl mx-auto">
            <h2 class="text-4xl font-bold text-center mb-6">🚀 Regístrate Ahora</h2>
            <p class="text-xl text-center mb-8 opacity-90">
                Déjanos tu email y te avisaremos cuando esté listo. 
                Los primeros 100 registrados tendrán acceso anticipado.
            </p>
            
            <!-- Formulario -->
            <form id="emailForm" class="bg-white rounded-lg p-8 shadow-2xl">
                <div class="mb-6">
                    <label for="email" class="block text-gray-700 font-semibold mb-2">Email</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        required
                        placeholder="tu@email.com"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-800"
                    >
                </div>
                <button 
                    type="submit" 
                    id="submitBtn"
                    class="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-4 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition duration-300 transform hover:scale-105"
                >
                    ¡Quiero Acceso Anticipado!
                </button>
                <p id="statusMessage" class="mt-4 text-center text-sm"></p>
            </form>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-8 px-4 text-center">
        <p class="text-sm opacity-75">© {datetime.now().year} {nombre}. Idea validada automáticamente.</p>
        <p class="text-xs opacity-50 mt-2">Generado con Idea Validator</p>
    </footer>

    <!-- Script para manejo del formulario -->
    <script>
        const form = document.getElementById('emailForm');
        const submitBtn = document.getElementById('submitBtn');
        const statusMessage = document.getElementById('statusMessage');

        form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            
            // Deshabilitar botón
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
            statusMessage.textContent = '';
            statusMessage.className = 'mt-4 text-center text-sm';

            try {{
                const response = await fetch('https://validationidea.vercel.app/api/submit-email', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        email: email,
                        idea: '{slug}',
                        timestamp: new Date().toISOString()
                    }})
                }});

                const data = await response.json();

                if (response.ok) {{
                    statusMessage.textContent = '✅ ¡Registrado! Revisa tu email.';
                    statusMessage.className = 'mt-4 text-center text-sm text-green-600 font-semibold';
                    form.reset();
                }} else {{
                    throw new Error(data.error || 'Error al registrar');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                statusMessage.textContent = '❌ Error al registrar. Inténtalo de nuevo.';
                statusMessage.className = 'mt-4 text-center text-sm text-red-600 font-semibold';
            }} finally {{
                submitBtn.disabled = false;
                submitBtn.textContent = '¡Quiero Acceso Anticipado!';
            }}
        }});
    </script>
</body>
</html>"""
    
    # Guardar archivo
    output_dir = 'landing-pages'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f'{output_dir}/{slug}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Landing generada: {filename}")
    return filename


def generate_all_landings(ideas_list):
    """
    Genera landings para una lista de ideas
    """
    generated_files = []
    
    for idea in ideas_list:
        try:
            filename = generate_landing(idea)
            generated_files.append(filename)
        except Exception as e:
            print(f"❌ Error generando landing para {idea.get('slug', 'unknown')}: {e}")
    
    return generated_files


if __name__ == "__main__":
    # Test con una idea de ejemplo
    test_idea = {
        'slug': 'test-idea',
        'nombre': 'Test SaaS Validator',
        'descripcion': 'Herramienta para validar ideas rápidamente',
        'problema': 'Es difícil saber si una idea SaaS tendrá éxito sin invertir meses de desarrollo',
        'solucion': 'Sistema automatizado que valida ideas en 48 horas con landing pages y métricas reales',
        'tam': '50M€',
        'sam': '5M€',
        'som': '500K€',
        'precio_sugerido': '49€/mes'
    }
    
    print("🧪 Generando landing de prueba...")
    generate_landing(test_idea)
    print("✅ Landing de prueba generada en landing-pages/test-idea.html")
