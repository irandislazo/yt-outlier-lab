"""
YT Outlier Lab — Punto de entrada.
Compatible con: desarrollo, cx_Freeze, PyInstaller.
Todos los errores se guardan en error_log.txt
"""
import os
import sys
import traceback
import webbrowser
import threading
import logging
from datetime import datetime

# ── Detectar modo de ejecución ──────────────────────────────────
if getattr(sys, 'frozen', False):
    # Ejecutable congelado (cx_Freeze / PyInstaller)
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    # cx_Freeze pone los datos en el mismo dir del exe
    BUNDLE_DIR = BASE_DIR
else:
    # Modo desarrollo
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

# Cambiar al directorio base (CRÍTICO: aquí se busca el .env y la DB)
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Configurar logging a archivo ────────────────────────────────
LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def show_error_and_exit(title, message):
    """Muestra un error visible al usuario y lo loguea."""
    logger.error(f"{title}: {message}")
    logger.error(traceback.format_exc())

    # Intentar mostrar ventana de error (si tkinter está disponible)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            title,
            f"{message}\n\n"
            f"Detalles completos en:\n{LOG_FILE}"
        )
        root.destroy()
    except Exception:
        pass

    # Mantener consola abierta si existe
    try:
        input("Presiona ENTER para salir...")
    except Exception:
        pass

    sys.exit(1)


# ── Capturar errores no manejados globalmente ───────────────────
def global_exception_handler(exc_type, exc_value, exc_tb):
    logger.critical(
        "Error no manejado",
        exc_info=(exc_type, exc_value, exc_tb)
    )
    show_error_and_exit(
        "YT Outlier Lab — Error fatal",
        f"{exc_type.__name__}: {exc_value}"
    )

sys.excepthook = global_exception_handler


# ── Iniciar la aplicación ───────────────────────────────────────
def main():
    try:
        logger.info("=" * 60)
        logger.info(f"YT Outlier Lab iniciando desde: {BASE_DIR}")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Modo frozen: {getattr(sys, 'frozen', False)}")
        logger.info("=" * 60)

        # Salida UTF-8
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")

        # Cargar .env
        from dotenv import load_dotenv
        env_path = os.path.join(BASE_DIR, ".env")
        load_dotenv(env_path)

        # Crear .env vacío si no existe
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("# YT Outlier Lab\n")
                f.write("YOUTUBE_API_KEY=\n")
            logger.warning(f".env creado en: {env_path}")

        # Verificar API Key
        api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        has_valid_key = bool(api_key) and api_key != "TU_API_KEY_AQUI"

        if has_valid_key:
            logger.info(f"✅ API Key configurada: {api_key[:8]}...")
        else:
            logger.warning(
                "⚠️  API Key NO configurada. "
                "Configúrala en: Configuración (⚙️) → Claves de API"
            )

        # Abrir navegador automáticamente
        def open_browser():
            try:
                webbrowser.open("http://localhost:8050")
            except Exception as e:
                logger.warning(f"No se pudo abrir navegador: {e}")

        threading.Timer(2.5, open_browser).start()

        logger.info("🌐 Servidor en: http://localhost:8050")

        # Importar y ejecutar la app
        from dashboard.app import app

        app.run(
            debug=False,
            host="127.0.0.1",
            port=8050,
            dev_tools_silence_routes_logging=True,
            use_reloader=False,  # CRÍTICO en modo frozen
        )

    except Exception as e:
        show_error_and_exit("YT Outlier Lab — Error al iniciar", str(e))


if __name__ == "__main__":
    main()