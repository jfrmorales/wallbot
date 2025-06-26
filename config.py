"""
Configuración centralizada para el bot de seguimiento de productos
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración del bot"""
    
    # Token del bot de Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Configuración de la base de datos
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/db.sqlite")
    
    # Configuración de Wallapop
    WALLAPOP_API_URL: str = "https://api.wallapop.com/api/v3/general/search"
    WALLAPOP_BASE_URL: str = "https://es.wallapop.com/item/"
    
    # Configuración de búsqueda
    DEFAULT_DISTANCE: str = "400"
    DEFAULT_PUBLISH_DATE: int = 24
    DEFAULT_ORDER: str = "newest"
    
    # Configuración de intervalos
    SEARCH_INTERVAL_SECONDS: int = int(os.getenv("SEARCH_INTERVAL", "300"))  # 5 minutos
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/wallbot.log")
    
    # Configuración de notificaciones
    MAX_NOTIFICATIONS_PER_HOUR: int = int(os.getenv("MAX_NOTIFICATIONS_PER_HOUR", "50"))
    
    # Configuración de limpieza de datos
    ITEM_CLEANUP_HOURS: int = int(os.getenv("ITEM_CLEANUP_HOURS", "24"))
    
    @classmethod
    def validate(cls) -> bool:
        """Valida que la configuración sea correcta"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN no está configurado")
        return True 