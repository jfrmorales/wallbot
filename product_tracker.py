"""
Servicio principal de seguimiento de productos
"""
import logging
import threading
import time
from typing import List, Optional
from datetime import datetime, timedelta
import schedule

from models import ProductSearch, Product, SearchResult
from database import DatabaseManager
from wallapop_client import WallapopClient
from notification_service import NotificationService
from config import Config

logger = logging.getLogger(__name__)

class ProductTracker:
    """Servicio principal para el seguimiento de productos"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.wallapop_client = WallapopClient()
        self.notification_service = NotificationService(Config.BOT_TOKEN)
        self.is_running = False
        self.search_thread = None
        
    def start(self):
        """Inicia el servicio de seguimiento"""
        if self.is_running:
            logger.warning("El servicio ya está ejecutándose")
            return
        
        self.is_running = True
        self.search_thread = threading.Thread(target=self._search_loop, daemon=True)
        self.search_thread.start()
        
        # Programar limpieza diaria
        schedule.every().day.at("02:00").do(self._cleanup_old_products)
        
        logger.info("Servicio de seguimiento de productos iniciado")
    
    def stop(self):
        """Detiene el servicio de seguimiento"""
        self.is_running = False
        if self.search_thread:
            self.search_thread.join(timeout=5)
        logger.info("Servicio de seguimiento de productos detenido")
    
    def _search_loop(self):
        """Bucle principal de búsqueda"""
        while self.is_running:
            try:
                logger.info("Iniciando ciclo de búsqueda...")
                self._process_all_searches()
                schedule.run_pending()
                
                logger.info(f"Esperando {Config.SEARCH_INTERVAL_SECONDS} segundos hasta la próxima búsqueda...")
                time.sleep(Config.SEARCH_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.error(f"Error en el bucle de búsqueda: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def _process_all_searches(self):
        """Procesa todas las búsquedas activas"""
        try:
            searches = self.db.get_all_active_searches()
            if not searches:
                logger.info("No hay búsquedas activas para procesar")
                return
            
            logger.info(f"Procesando {len(searches)} búsquedas activas")
            
            for search in searches:
                try:
                    self._process_search(search)
                except Exception as e:
                    logger.error(f"Error procesando búsqueda {search.keywords}: {e}")
                    continue
                
                # Pequeña pausa entre búsquedas para no sobrecargar la API
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Error procesando búsquedas: {e}")
    
    def _process_search(self, search: ProductSearch):
        """Procesa una búsqueda específica"""
        try:
            logger.info(f"Procesando búsqueda: {search.keywords} para chat {search.chat_id}")
            
            # Buscar productos en Wallapop usando Playwright
            search_results = self.wallapop_client.search_products_playwright(search)
            
            if not search_results:
                logger.info(f"No se encontraron productos para: {search.keywords}")
                return
            
            logger.info(f"Encontrados {len(search_results)} productos para: {search.keywords}")
            
            # Procesar cada producto encontrado
            for result in search_results:
                self._process_product_result(result, search.chat_id)
                
        except Exception as e:
            logger.error(f"Error procesando búsqueda {search.keywords}: {e}")
    
    def _process_product_result(self, result: SearchResult, chat_id: str):
        """Procesa un resultado de producto específico"""
        try:
            # Verificar si el producto ya existe en la base de datos
            existing_product = self.db.get_product(result.id, chat_id)
            
            if existing_product is None:
                # Producto nuevo
                self._handle_new_product(result, chat_id)
            else:
                # Producto existente - verificar cambios de precio
                self._handle_existing_product(result, existing_product)
                
        except Exception as e:
            logger.error(f"Error procesando producto {result.id}: {e}")
    
    def _handle_new_product(self, result: SearchResult, chat_id: str):
        """Maneja un producto nuevo"""
        try:
            # Crear objeto Product
            product = Product(
                item_id=result.id,
                chat_id=chat_id,
                title=result.title,
                price=result.price,
                url=result.web_slug,
                user_id=result.user_id
            )
            
            # Guardar en base de datos
            if self.db.add_product(product):
                # Enviar notificación
                self.notification_service.notify_new_product(product)
                logger.info(f"Nuevo producto añadido: {result.title} - {result.price}€")
            else:
                logger.error(f"Error al guardar nuevo producto: {result.id}")
                
        except Exception as e:
            logger.error(f"Error manejando nuevo producto {result.id}: {e}")
    
    def _handle_existing_product(self, result: SearchResult, existing_product: Product):
        """Maneja un producto existente"""
        try:
            # Verificar si el precio ha bajado
            if result.price < existing_product.price:
                # Crear objeto Product con el nuevo precio
                updated_product = Product(
                    item_id=result.id,
                    chat_id=existing_product.chat_id,
                    title=result.title,
                    price=result.price,
                    url=result.web_slug,
                    user_id=result.user_id,
                    observations=f"Precio anterior: {existing_product.price}€"
                )
                
                # Actualizar en base de datos
                if self.db.update_product_price(result.id, result.price, f"Precio anterior: {existing_product.price}€"):
                    # Enviar notificación de bajada de precio
                    self.notification_service.notify_price_drop(updated_product, existing_product.price)
                    logger.info(f"Bajada de precio detectada: {result.title} - {existing_product.price}€ → {result.price}€")
                else:
                    logger.error(f"Error al actualizar precio del producto: {result.id}")
                    
        except Exception as e:
            logger.error(f"Error manejando producto existente {result.id}: {e}")
    
    def add_search(self, chat_id: str, keywords: str, min_price: Optional[float] = None, 
                  max_price: Optional[float] = None, category_ids: Optional[str] = None,
                  username: Optional[str] = None, name: Optional[str] = None) -> bool:
        """Añade una nueva búsqueda"""
        try:
            # Crear objeto ProductSearch (la validación se hace automáticamente)
            search = ProductSearch(
                chat_id=chat_id,
                keywords=keywords,
                min_price=min_price,
                max_price=max_price,
                category_ids=category_ids,
                username=username,
                name=name
            )
            
            # Guardar en base de datos
            if self.db.add_search(search):
                # Enviar notificación de confirmación
                self.notification_service.notify_search_added(chat_id, keywords, min_price, max_price)
                logger.info(f"Búsqueda añadida: {keywords} para chat {chat_id}")
                return True
            else:
                logger.error(f"Error al añadir búsqueda: {keywords}")
                return False
                
        except Exception as e:
            logger.error(f"Error añadiendo búsqueda: {e}")
            self.notification_service.send_error_message(chat_id, str(e))
            return False
    
    def remove_search(self, chat_id: str, keywords: str) -> bool:
        """Elimina una búsqueda"""
        try:
            if self.db.deactivate_search(chat_id, keywords):
                self.notification_service.notify_search_removed(chat_id, keywords)
                logger.info(f"Búsqueda eliminada: {keywords} para chat {chat_id}")
                return True
            else:
                logger.error(f"Error al eliminar búsqueda: {keywords}")
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando búsqueda: {e}")
            return False
    
    def get_user_searches(self, chat_id: str) -> List[ProductSearch]:
        """Obtiene las búsquedas de un usuario"""
        try:
            return self.db.get_searches_by_chat(chat_id)
        except Exception as e:
            logger.error(f"Error obteniendo búsquedas del usuario {chat_id}: {e}")
            return []
    
    def _cleanup_old_products(self):
        """Limpia productos antiguos de la base de datos"""
        try:
            deleted_count = self.db.cleanup_old_products(Config.ITEM_CLEANUP_HOURS)
            logger.info(f"Limpieza completada: {deleted_count} productos eliminados")
        except Exception as e:
            logger.error(f"Error en limpieza de productos: {e}")
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del sistema"""
        try:
            # Esta funcionalidad se puede implementar más adelante
            return {
                "active_searches": len(self.db.get_all_active_searches()),
                "is_running": self.is_running
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {} 