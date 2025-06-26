"""
Bot principal de Telegram para seguimiento de productos
"""
import logging
import re
from typing import Optional, Tuple
from datetime import datetime
import telebot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from config import Config
from product_tracker import ProductTracker
from notification_service import NotificationService

# Configurar logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SearchStates(StatesGroup):
    """Estados para el flujo de añadir búsqueda"""
    waiting_for_keywords = State()
    waiting_for_price_range = State()

class ProductTrackingBot:
    """Bot principal de Telegram para seguimiento de productos"""
    
    def __init__(self):
        # Configurar bot con manejo de estados
        state_storage = StateMemoryStorage()
        self.bot = telebot.TeleBot(Config.BOT_TOKEN, state_storage=state_storage)
        
        # Inicializar servicios
        self.product_tracker = ProductTracker()
        self.notification_service = NotificationService(Config.BOT_TOKEN)
        
        # Configurar handlers
        self._setup_handlers()
        
        logger.info("Bot inicializado correctamente")
    
    def _setup_handlers(self):
        """Configura todos los handlers del bot"""
        
        # Comandos básicos
        @self.bot.message_handler(commands=['start', 'help', 'h'])
        def handle_start_help(message):
            """Maneja comandos de inicio y ayuda"""
            self.notification_service.send_help_message(str(message.chat.id))
        
        @self.bot.message_handler(commands=['add', 'a'])
        def handle_add_search(message):
            """Maneja el comando para añadir búsqueda"""
            try:
                chat_id = str(message.chat.id)
                text = message.text.strip()
                
                # Parsear comando: /add producto,min-max
                parts = text.split(' ', 1)
                if len(parts) < 2:
                    self.notification_service.send_error_message(
                        chat_id, 
                        "Formato incorrecto. Usa: /add producto,min-max\nEjemplo: /add zapatos rojos,10-50"
                    )
                    return
                
                # Parsear parámetros
                params = parts[1].split(',')
                keywords = params[0].strip()
                
                if not keywords:
                    self.notification_service.send_error_message(chat_id, "Debes especificar palabras clave")
                    return
                
                # Parsear rango de precio
                min_price = None
                max_price = None
                
                if len(params) > 1 and params[1].strip():
                    price_range = params[1].strip()
                    if '-' in price_range:
                        price_parts = price_range.split('-')
                        try:
                            if price_parts[0].strip():
                                min_price = float(price_parts[0].strip())
                            if len(price_parts) > 1 and price_parts[1].strip():
                                max_price = float(price_parts[1].strip())
                        except ValueError:
                            self.notification_service.send_error_message(
                                chat_id, 
                                "Formato de precio incorrecto. Usa números separados por guión (ej: 10-50)"
                            )
                            return
                
                # Validar rango de precio
                if min_price is not None and max_price is not None and min_price >= max_price:
                    self.notification_service.send_error_message(
                        chat_id, 
                        "El precio mínimo debe ser menor que el precio máximo"
                    )
                    return
                
                # Añadir búsqueda
                success = self.product_tracker.add_search(
                    chat_id=chat_id,
                    keywords=keywords,
                    min_price=min_price,
                    max_price=max_price,
                    username=message.from_user.username,
                    name=message.from_user.first_name
                )
                
                if not success:
                    self.notification_service.send_error_message(
                        chat_id, 
                        "Error al añadir la búsqueda. Intenta de nuevo."
                    )
                    
            except Exception as e:
                logger.error(f"Error en handle_add_search_command: {e}")
                self.notification_service.send_error_message(
                    str(message.chat.id), 
                    "Error interno del bot. Intenta de nuevo."
                )
        
        @self.bot.message_handler(commands=['del', 'delete', 'd'])
        def handle_delete_search(message):
            """Maneja el comando para eliminar búsqueda"""
            self._handle_delete_search_command(message)
        
        @self.bot.message_handler(commands=['list', 'lis', 'l'])
        def handle_list_searches(message):
            """Maneja el comando para listar búsquedas"""
            self._handle_list_searches_command(message)
        
        @self.bot.message_handler(commands=['stats', 's'])
        def handle_stats(message):
            """Maneja el comando para mostrar estadísticas"""
            self._handle_stats_command(message)
        
        @self.bot.message_handler(commands=['testcookies'])
        def handle_test_cookies(message):
            """Maneja el comando para probar búsquedas con cookies"""
            try:
                chat_id = str(message.chat.id)
                text = message.text.strip()
                
                # Parsear comando: /testcookies "cookies" producto
                parts = text.split(' ', 2)
                if len(parts) < 3:
                    self.notification_service.send_error_message(
                        chat_id, 
                        "Formato incorrecto. Usa: /testcookies \"cookies\" producto\n"
                        "Ejemplo: /testcookies \"session=abc123; user=xyz\" iPhone"
                    )
                    return
                
                cookies = parts[1].strip('"')
                keywords = parts[2].strip()
                
                if not cookies or not keywords:
                    self.notification_service.send_error_message(chat_id, "Debes especificar cookies y producto")
                    return
                
                # Crear búsqueda temporal para probar
                from models import ProductSearch
                search = ProductSearch(
                    chat_id=chat_id,
                    keywords=keywords,
                    min_price=100.0,
                    max_price=500.0
                )
                
                # Probar con cookies
                results = self.product_tracker.wallapop_client.search_products_playwright_with_cookies(search, cookies)
                
                if results:
                    message_text = f"✅ Encontrados {len(results)} productos para '{keywords}':\n\n"
                    for i, result in enumerate(results[:5], 1):
                        message_text += f"{i}. {result.title} - {result.price}€\n"
                    if len(results) > 5:
                        message_text += f"\n... y {len(results) - 5} más"
                else:
                    message_text = f"❌ No se encontraron productos para '{keywords}'"
                
                self.notification_service._send_telegram_message(chat_id, message_text)
                
            except Exception as e:
                logger.error(f"Error en handle_test_cookies: {e}")
                self.notification_service.send_error_message(
                    str(message.chat.id), 
                    "Error interno del bot. Intenta de nuevo."
                )
        
        # Handler para texto libre (búsquedas rápidas)
        @self.bot.message_handler(func=lambda message: True)
        def handle_text_message(message):
            """Maneja mensajes de texto como búsquedas rápidas"""
            if not message.text.startswith('/'):
                self._handle_quick_search(message)
    
    def _handle_delete_search_command(self, message):
        """Maneja el comando /del"""
        try:
            chat_id = str(message.chat.id)
            text = message.text.strip()
            
            # Parsear comando: /del producto
            parts = text.split(' ', 1)
            if len(parts) < 2:
                self.notification_service.send_error_message(
                    chat_id, 
                    "Formato incorrecto. Usa: /del producto\nEjemplo: /del zapatos rojos"
                )
                return
            
            keywords = parts[1].strip()
            if not keywords:
                self.notification_service.send_error_message(chat_id, "Debes especificar qué búsqueda eliminar")
                return
            
            # Eliminar búsqueda
            success = self.product_tracker.remove_search(chat_id, keywords)
            
            if not success:
                self.notification_service.send_error_message(
                    chat_id, 
                    f"No se encontró la búsqueda '{keywords}' o error al eliminarla"
                )
                
        except Exception as e:
            logger.error(f"Error en handle_delete_search_command: {e}")
            self.notification_service.send_error_message(
                str(message.chat.id), 
                "Error interno del bot. Intenta de nuevo."
            )
    
    def _handle_list_searches_command(self, message):
        """Maneja el comando /list"""
        try:
            chat_id = str(message.chat.id)
            
            # Obtener búsquedas del usuario
            searches = self.product_tracker.get_user_searches(chat_id)
            
            # Enviar lista
            self.notification_service.send_search_list(chat_id, searches)
            
        except Exception as e:
            logger.error(f"Error en handle_list_searches_command: {e}")
            self.notification_service.send_error_message(
                str(message.chat.id), 
                "Error interno del bot. Intenta de nuevo."
            )
    
    def _handle_stats_command(self, message):
        """Maneja el comando /stats"""
        try:
            chat_id = str(message.chat.id)
            stats = self.product_tracker.get_stats()
            
            message_text = (
                f"📊 *Estadísticas del Bot*\n\n"
                f"🔍 Búsquedas activas: {stats.get('active_searches', 0)}\n"
                f"🔄 Estado: {'Activo' if stats.get('is_running', False) else 'Inactivo'}\n"
                f"⏰ Última actualización: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            self.notification_service._send_telegram_message(chat_id, message_text)
            
        except Exception as e:
            logger.error(f"Error en handle_stats_command: {e}")
            self.notification_service.send_error_message(
                str(message.chat.id), 
                "Error interno del bot. Intenta de nuevo."
            )
    
    def _handle_quick_search(self, message):
        """Maneja búsquedas rápidas (texto sin comando)"""
        try:
            chat_id = str(message.chat.id)
            keywords = message.text.strip()
            
            if not keywords:
                return
            
            # Añadir búsqueda sin filtros de precio
            success = self.product_tracker.add_search(
                chat_id=chat_id,
                keywords=keywords,
                username=message.from_user.username,
                name=message.from_user.first_name
            )
            
            if not success:
                self.notification_service.send_error_message(
                    chat_id, 
                    "Error al añadir la búsqueda. Intenta de nuevo."
                )
                
        except Exception as e:
            logger.error(f"Error en handle_quick_search: {e}")
            self.notification_service.send_error_message(
                str(message.chat.id), 
                "Error interno del bot. Intenta de nuevo."
            )
    
    def start(self):
        """Inicia el bot"""
        try:
            # Validar configuración
            Config.validate()
            
            # Iniciar el servicio de seguimiento
            self.product_tracker.start()
            
            logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
            
            # Iniciar polling del bot
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
            
        except KeyboardInterrupt:
            logger.info("Deteniendo bot...")
        except Exception as e:
            logger.error(f"Error iniciando bot: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el bot"""
        try:
            self.product_tracker.stop()
            logger.info("Bot detenido")
        except Exception as e:
            logger.error(f"Error deteniendo bot: {e}")

def main():
    """Función principal"""
    try:
        bot = ProductTrackingBot()
        bot.start()
    except Exception as e:
        logger.error(f"Error en main: {e}")

if __name__ == "__main__":
    main() 