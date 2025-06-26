"""
Módulo de base de datos mejorado para el bot de seguimiento de productos
"""
import sqlite3
import logging
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta
import time

from models import ProductSearch, Product, Notification
from config import Config

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos"""
    pass

class DatabaseManager:
    """Gestor de base de datos mejorado"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._setup_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones de base de datos"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Error de base de datos: {e}")
            raise DatabaseError(f"Error de base de datos: {e}")
        finally:
            if conn:
                conn.close()
    
    def _setup_database(self):
        """Configura las tablas de la base de datos"""
        with self.get_connection() as conn:
            # Tabla de búsquedas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS product_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    min_price REAL,
                    max_price REAL,
                    category_ids TEXT,
                    distance TEXT DEFAULT '400',
                    publish_date INTEGER DEFAULT 24,
                    order_by TEXT DEFAULT 'newest',
                    username TEXT,
                    name TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, keywords)
                )
            """)
            
            # Tabla de productos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    item_id TEXT NOT NULL,
                    chat_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    url TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    publish_date INTEGER,
                    observations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (item_id, chat_id)
                )
            """)
            
            # Tabla de notificaciones
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para mejorar rendimiento
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_chat_id ON products(chat_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_searches_chat_id ON product_searches(chat_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_searches_active ON product_searches(active)")
            
            conn.commit()
            logger.info("Base de datos configurada correctamente")
    
    def add_search(self, search: ProductSearch) -> bool:
        """Añade una nueva búsqueda"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO product_searches 
                    (chat_id, keywords, min_price, max_price, category_ids, distance, 
                     publish_date, order_by, username, name, active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    search.chat_id, search.keywords, search.min_price, search.max_price,
                    search.category_ids, search.distance, search.publish_date, search.order,
                    search.username, search.name, search.active, datetime.now()
                ))
                conn.commit()
                logger.info(f"Búsqueda añadida: {search.keywords} para chat {search.chat_id}")
                return True
        except Exception as e:
            logger.error(f"Error al añadir búsqueda: {e}")
            return False
    
    def get_searches_by_chat(self, chat_id: str) -> List[ProductSearch]:
        """Obtiene todas las búsquedas activas de un chat"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM product_searches 
                    WHERE chat_id = ? AND active = 1
                    ORDER BY created_at DESC
                """, (chat_id,))
                
                searches = []
                for row in cursor.fetchall():
                    search = ProductSearch(
                        chat_id=row['chat_id'],
                        keywords=row['keywords'],
                        min_price=row['min_price'],
                        max_price=row['max_price'],
                        category_ids=row['category_ids'],
                        distance=row['distance'],
                        publish_date=row['publish_date'],
                        order=row['order_by'],
                        username=row['username'],
                        name=row['name'],
                        active=bool(row['active'])
                    )
                    searches.append(search)
                
                return searches
        except Exception as e:
            logger.error(f"Error al obtener búsquedas: {e}")
            return []
    
    def get_all_active_searches(self) -> List[ProductSearch]:
        """Obtiene todas las búsquedas activas"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM product_searches 
                    WHERE active = 1
                    ORDER BY created_at DESC
                """)
                
                searches = []
                for row in cursor.fetchall():
                    search = ProductSearch(
                        chat_id=row['chat_id'],
                        keywords=row['keywords'],
                        min_price=row['min_price'],
                        max_price=row['max_price'],
                        category_ids=row['category_ids'],
                        distance=row['distance'],
                        publish_date=row['publish_date'],
                        order=row['order_by'],
                        username=row['username'],
                        name=row['name'],
                        active=bool(row['active'])
                    )
                    searches.append(search)
                
                return searches
        except Exception as e:
            logger.error(f"Error al obtener todas las búsquedas: {e}")
            return []
    
    def deactivate_search(self, chat_id: str, keywords: str) -> bool:
        """Desactiva una búsqueda"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE product_searches 
                    SET active = 0, updated_at = ? 
                    WHERE chat_id = ? AND keywords = ?
                """, (datetime.now(), chat_id, keywords))
                conn.commit()
                logger.info(f"Búsqueda desactivada: {keywords} para chat {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Error al desactivar búsqueda: {e}")
            return False
    
    def add_product(self, product: Product) -> bool:
        """Añade un nuevo producto"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO products 
                    (item_id, chat_id, title, price, url, user_id, publish_date, 
                     observations, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product.item_id, product.chat_id, product.title, product.price,
                    product.url, product.user_id, product.publish_date,
                    product.observations, datetime.now()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error al añadir producto: {e}")
            return False
    
    def get_product(self, item_id: str, chat_id: str) -> Optional[Product]:
        """Obtiene un producto específico"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM products 
                    WHERE item_id = ? AND chat_id = ?
                """, (item_id, chat_id))
                
                row = cursor.fetchone()
                if row:
                    return Product(
                        item_id=row['item_id'],
                        chat_id=row['chat_id'],
                        title=row['title'],
                        price=row['price'],
                        url=row['url'],
                        user_id=row['user_id'],
                        publish_date=row['publish_date'],
                        observations=row['observations']
                    )
                return None
        except Exception as e:
            logger.error(f"Error al obtener producto: {e}")
            return None
    
    def update_product_price(self, item_id: str, new_price: float, observations: str = None) -> bool:
        """Actualiza el precio de un producto"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE products 
                    SET price = ?, observations = ?, updated_at = ? 
                    WHERE item_id = ?
                """, (new_price, observations, datetime.now(), item_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error al actualizar precio: {e}")
            return False
    
    def cleanup_old_products(self, hours: int = 24) -> int:
        """Limpia productos antiguos"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM products 
                    WHERE created_at < ?
                """, (cutoff_time,))
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Eliminados {deleted_count} productos antiguos")
                return deleted_count
        except Exception as e:
            logger.error(f"Error al limpiar productos: {e}")
            return 0
    
    def add_notification(self, notification: Notification) -> bool:
        """Añade una nueva notificación"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO notifications 
                    (chat_id, message, product_id, notification_type)
                    VALUES (?, ?, ?, ?)
                """, (
                    notification.chat_id, notification.message,
                    notification.product_id, notification.notification_type
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error al añadir notificación: {e}")
            return False
    
    def get_pending_notifications(self) -> List[Notification]:
        """Obtiene notificaciones pendientes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM notifications 
                    WHERE sent = 0
                    ORDER BY created_at ASC
                """)
                
                notifications = []
                for row in cursor.fetchall():
                    notification = Notification(
                        chat_id=row['chat_id'],
                        message=row['message'],
                        product_id=row['product_id'],
                        notification_type=row['notification_type']
                    )
                    notifications.append(notification)
                
                return notifications
        except Exception as e:
            logger.error(f"Error al obtener notificaciones: {e}")
            return []
    
    def mark_notification_sent(self, notification_id: int) -> bool:
        """Marca una notificación como enviada"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE notifications 
                    SET sent = 1 
                    WHERE id = ?
                """, (notification_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error al marcar notificación: {e}")
            return False 