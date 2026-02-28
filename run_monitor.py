import os
import sys
import time
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

MINUTOS_ENTRE_IDEAS = 30  # Genera una idea cada 30 minutos

def log(mensaje):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensaje}", flush=True)

def ejecutar_una_idea():
    try:
        from run_batch import ejecutar_batch
        resultado = ejecutar_batch()
        if resultado:
            log("✅ Idea TOP generada y sincronizada")
        else:
            log("⚠️ Batch completado sin idea TOP (normal, se reintentará)")
        return True
    except Exception as e:
        log(f"❌ Error en batch: {e}")
        return False

def main():
    log("=" * 60)
    log("🚀 MONITOR AUTOMÁTICO - validationidea")
    log(f"⏰ Genera ideas cada {MINUTOS_ENTRE_IDEAS} minutos")
    log("=" * 60)

    ciclo = 1
    while True:
        log(f"\n🔄 CICLO #{ciclo} - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        ejecutar_una_idea()
        
        proxima = MINUTOS_ENTRE_IDEAS * 60
        log(f"😴 Esperando {MINUTOS_ENTRE_IDEAS} minutos... (Ctrl+C para parar)")
        
        # Espera en trozos de 60s para que no parezca colgado
        for i in range(MINUTOS_ENTRE_IDEAS):
            time.sleep(60)
            restantes = MINUTOS_ENTRE_IDEAS - i - 1
            if restantes > 0 and restantes % 5 == 0:
                log(f"⏳ {restantes} minutos para próxima idea...")
        
        ciclo += 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 Monitor parado por el usuario")
        sys.exit(0)
