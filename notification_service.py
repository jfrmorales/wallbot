"""
Servicio de notificaciones para el bot de Telegram
"""
import logging
import locale
from typing import Optional
import requests
from datetime import datetime

from models import Product, Notification
from config import Config

logger = logging.getLogger(__name__)

# Configurar locale para formato de moneda
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES')
    except locale.Error:
        logger.warning("No se pudo configurar locale español, usando configuración por defecto")

class NotificationService:
    """Servicio para manejar notificaciones de Telegram"""
    
    # Emojis para las notificaciones
    ICONS = {
        'new_product': '🎯',
        'price_drop': '💥',
        'warning': '⚠️',
        'info': 'ℹ️',
        'success': '✅',
        'error': '❌'
    }
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}/"
        self.notification_count = 0
        self.last_reset = datetime.now()
    
    def _format_price(self, price: float) -> str:
        """Formatea el precio en formato de moneda"""
        try:
            return locale.currency(price, grouping=True)
        except:
            return f"{price:.2f}€"
    
    def _check_rate_limit(self) -> bool:
        """Verifica el límite de notificaciones por hora"""
        now = datetime.now()
        if (now - self.last_reset).total_seconds() > 3600:  # 1 hora
            self.notification_count = 0
            self.last_reset = now
        
        if self.notification_count >= Config.MAX_NOTIFICATIONS_PER_HOUR:
            logger.warning("Límite de notificaciones por hora alcanzado")
            return False
        
        return True
    
    def _send_telegram_message(self, chat_id: str, message: str, parse_mode: str = 'Markdown') -> bool:
        """Envía un mensaje a Telegram"""
        if not self._check_rate_limit():
            return False
        
        try:
            url = f"{self.api_url}sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                self.notification_count += 1
                logger.info(f"Mensaje enviado a chat {chat_id}")
                return True
            else:
                logger.error(f"Error al enviar mensaje: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error al enviar mensaje a Telegram: {e}")
            return False
    
    def notify_new_product(self, product: Product) -> bool:
        """Notifica sobre un nuevo producto encontrado"""
        try:
            formatted_price = self._format_price(product.price)
            
            message = (
                f"{self.ICONS['new_product']} *Nuevo producto encontrado!*\n\n"
                f"*{product.title}*\n"
                f"💰 Precio: {formatted_price}\n"
                f"🔗 [Ver en Wallapop]({Config.WALLAPOP_BASE_URL}{product.url})\n"
                f"⏰ {datetime.now().strftime('%H:%M')}"
            )
            
            return self._send_telegram_message(product.chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al crear notificación de nuevo producto: {e}")
            return False
    
    def notify_price_drop(self, product: Product, old_price: float) -> bool:
        """Notifica sobre una bajada de precio"""
        try:
            new_price_formatted = self._format_price(product.price)
            old_price_formatted = self._format_price(old_price)
            price_difference = old_price - product.price
            price_difference_formatted = self._format_price(price_difference)
            
            message = (
                f"{self.ICONS['price_drop']} *¡Bajada de precio!*\n\n"
                f"*{product.title}*\n"
                f"💰 Precio anterior: {old_price_formatted}\n"
                f"💰 Precio actual: {new_price_formatted}\n"
                f"📉 Ahorro: {price_difference_formatted}\n"
                f"🔗 [Ver en Wallapop]({Config.WALLAPOP_BASE_URL}{product.url})\n"
                f"⏰ {datetime.now().strftime('%H:%M')}"
            )
            
            return self._send_telegram_message(product.chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al crear notificación de bajada de precio: {e}")
            return False
    
    def notify_search_added(self, chat_id: str, keywords: str, min_price: Optional[float] = None, 
                          max_price: Optional[float] = None) -> bool:
        """Notifica que se ha añadido una nueva búsqueda"""
        try:
            price_info = ""
            if min_price is not None or max_price is not None:
                price_range = []
                if min_price is not None:
                    try:
                        price_range.append(self._format_price(float(min_price)))
                    except Exception:
                        price_range.append(str(min_price))
                if max_price is not None:
                    try:
                        price_range.append(self._format_price(float(max_price)))
                    except Exception:
                        price_range.append(str(max_price))
                price_info = f"\n💰 Rango de precio: {' - '.join(price_range)}"
            
            message = (
                f"{self.ICONS['success']} *Búsqueda añadida correctamente*\n\n"
                f"🔍 *{keywords}*{price_info}\n"
                f"✅ Recibirás notificaciones cuando encuentre productos que coincidan"
            )
            
            return self._send_telegram_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al crear notificación de búsqueda añadida: {e}")
            return False
    
    def notify_search_removed(self, chat_id: str, keywords: str) -> bool:
        """Notifica que se ha eliminado una búsqueda"""
        try:
            message = (
                f"{self.ICONS['info']} *Búsqueda eliminada*\n\n"
                f"🔍 *{keywords}*\n"
                f"❌ Ya no recibirás notificaciones para esta búsqueda"
            )
            
            return self._send_telegram_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al crear notificación de búsqueda eliminada: {e}")
            return False
    
    def send_help_message(self, chat_id: str) -> bool:
        """Envía el mensaje de ayuda"""
        try:
            message = (
                f"{self.ICONS['info']} *Bot de Seguimiento de Productos*\n\n"
                f"*Comandos disponibles:*\n\n"
                f"🔍 *Añadir búsqueda:*\n"
                f"`/add producto,min-max`\n"
                f"Ejemplo: `/add zapatos rojos,10-50`\n\n"
                f"🗑️ *Eliminar búsqueda:*\n"
                f"`/del producto`\n"
                f"Ejemplo: `/del zapatos rojos`\n\n"
                f"📋 *Listar búsquedas:*\n"
                f"`/list` o `/lis`\n\n"
                f"❓ *Ayuda:*\n"
                f"`/help` o `/start`\n\n"
                f"*Funcionalidades:*\n"
                f"• Notificaciones de productos nuevos\n"
                f"• Alertas de bajadas de precio\n"
                f"• Filtros por precio y categoría\n"
                f"• Búsquedas personalizadas"
            )
            
            return self._send_telegram_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al enviar mensaje de ayuda: {e}")
            return False
    
    def send_error_message(self, chat_id: str, error_message: str) -> bool:
        """Envía un mensaje de error"""
        try:
            message = (
                f"{self.ICONS['error']} *Error*\n\n"
                f"❌ {error_message}\n\n"
                f"Por favor, intenta de nuevo o contacta al administrador."
            )
            
            return self._send_telegram_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al enviar mensaje de error: {e}")
            return False
    
    def send_search_list(self, chat_id: str, searches: list) -> bool:
        """Envía la lista de búsquedas activas"""
        try:
            if not searches:
                message = (
                    f"{self.ICONS['info']} *No tienes búsquedas activas*\n\n"
                    f"Usa `/add producto,precio` para añadir tu primera búsqueda"
                )
            else:
                message = f"{self.ICONS['info']} *Tus búsquedas activas:*\n\n"
                
                for i, search in enumerate(searches, 1):
                    price_info = ""
                    if search.min_price is not None or search.max_price is not None:
                        min_price = search.min_price or 0
                        max_price = search.max_price or "∞"
                        price_info = f" ({min_price}-{max_price}€)"
                    
                    message += f"{i}. *{search.keywords}*{price_info}\n"
                
                message += f"\nUsa `/del producto` para eliminar una búsqueda"
            
            return self._send_telegram_message(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error al enviar lista de búsquedas: {e}")
            return False 