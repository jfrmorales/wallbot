#!/usr/bin/env python3
"""
Archivo principal para ejecutar el bot de seguimiento de productos
"""
import sys
import os
import logging
from pathlib import Path

# Añadir el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import ProductTrackingBot
from config import Config

def setup_logging():
    """Configura el sistema de logging"""
    # Crear directorio de logs si no existe
    log_dir = Path(Config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

def main():
    """Función principal"""
    try:
        # Configurar logging
        setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info("Iniciando bot de seguimiento de productos...")
        
        # Crear y ejecutar el bot
        bot = ProductTrackingBot()
        bot.start()
        
    except KeyboardInterrupt:
        print("\nBot detenido por el usuario")
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 