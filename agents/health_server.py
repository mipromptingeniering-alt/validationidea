"""
health_server.py - Endpoint HTTP para Railway keepalive
Evita que Railway duerma el contenedor por inactividad.
"""
import os, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT = int(os.environ.get("PORT", 8080))

_start_time = datetime.now()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/ping"):
            uptime = str(datetime.now() - _start_time).split(".")[0]
            payload = {
                "status":    "ok",
                "service":   "ValidationIdea v5",
                "uptime":    uptime,
                "timestamp": datetime.now().isoformat(),
            }
            try:
                from agents.knowledge_base import get_stats
                s = get_stats()
                payload["kb_ideas"]        = s.get("total_ideas", 0)
                payload["score_promedio"]  = s.get("score_promedio", 0)
            except: pass
            try:
                from agents.watchdog import get_diagnostico
                d = get_diagnostico()
                payload["timeouts_consecutivos"] = d.get("consecutive_timeouts", 0)
                payload["modo_emergencia"]        = d.get("modo_emergencia", False)
                payload["ultimo_exito"]           = d.get("last_success", "nunca")
            except: pass
            try:
                from agents.verticales_rotacion import get_stats_rotacion
                payload["rotacion_vertical"] = get_stats_rotacion()
            except: pass

            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # Silenciar logs HTTP

def iniciar_health_server():
    """Arranca el servidor en hilo daemon — no bloquea el proceso principal."""
    def _run():
        try:
            server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
            print(f"🌐 Health server en puerto {PORT}")
            server.serve_forever()
        except Exception as e:
            print(f"Health server error: {e}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t

# fin agents/health_server.py
