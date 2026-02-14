# Dentro de la función generate_landing(), en la sección del formulario:

formulario_html = f"""
<section id="registro" class="cta-section">
    <div class="cta-container">
        <h2>Únete a los primeros 100</h2>
        <p class="cta-subtitle">Consigue acceso anticipado con 70% de descuento para siempre.</p>
        
        <div class="urgency-banner">
            ⏰ Solo quedan <span id="plazas-restantes">23</span> plazas
        </div>
        
        <form id="waitlist-form" class="waitlist-form">
            <input 
                type="email" 
                id="email-input"
                placeholder="📧 tu@email.com" 
                required
                autocomplete="email"
            >
            <button type="submit" id="submit-btn" class="cta-button">
                🚀 ¡Quiero mi 70% de Descuento!
            </button>
        </form>
        
        <div id="form-message" class="form-message"></div>
        
        <p class="privacy-note">🔒 No spam. Cancelar cuando quieras.</p>
    </div>
</section>

<style>
.form-message {{
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
    display: none;
}}

.form-message.success {{
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
    display: block;
}}

.form-message.error {{
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    display: block;
}}

.form-message.loading {{
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
    display: block;
}}

#submit-btn:disabled {{
    opacity: 0.6;
    cursor: not-allowed;
}}
</style>

<script>
document.getElementById('waitlist-form').addEventListener('submit', async (e) => {{
    e.preventDefault();
    
    const emailInput = document.getElementById('email-input');
    const submitBtn = document.getElementById('submit-btn');
    const formMessage = document.getElementById('form-message');
    const email = emailInput.value.trim();
    
    // Validación básica
    if (!email) {{
        formMessage.className = 'form-message error';
        formMessage.textContent = '❌ Por favor, introduce tu email.';
        return;
    }}
    
    // Deshabilitar botón
    submitBtn.disabled = true;
    formMessage.className = 'form-message loading';
    formMessage.textContent = '⏳ Registrando...';
    
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
        
        if (response.ok && data.success) {{
            formMessage.className = 'form-message success';
            formMessage.textContent = '✅ ¡Registrado! Revisa tu email en 24h.';
            emailInput.value = '';
            
            // Actualizar plazas
            const plazasEl = document.getElementById('plazas-restantes');
            if (plazasEl) {{
                const plazas = parseInt(plazasEl.textContent) - 1;
                plazasEl.textContent = Math.max(1, plazas);
            }}
        }} else {{
            throw new Error(data.error || 'Error desconocido');
        }}
    }} catch (error) {{
        console.error('Error:', error);
        formMessage.className = 'form-message error';
        formMessage.textContent = '❌ Error al registrar. Inténtalo de nuevo o contacta: contacto@tudominio.com';
    }} finally {{
        submitBtn.disabled = false;
    }}
}});
</script>
"""
