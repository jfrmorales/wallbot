#!/usr/bin/env python3
"""
Script de migración de WallBot v1.0 a v2.0
Migra la base de datos y configuración del formato anterior al nuevo
"""
import sqlite3
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationManager:
    """Gestor de migración de v1.0 a v2.0"""
    
    def __init__(self, old_db_path="/data/db.sqlite", new_db_path="/data/db_v2.sqlite"):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        
    def backup_old_database(self):
        """Crea un backup de la base de datos anterior"""
        if os.path.exists(self.old_db_path):
            backup_path = f"{self.old_db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.old_db_path, backup_path)
            logger.info(f"Backup creado: {backup_path}")
            return backup_path
        else:
            logger.warning(f"Base de datos anterior no encontrada: {self.old_db_path}")
            return None
    
    def migrate_chat_searches(self, old_conn, new_conn):
        """Migra las búsquedas de chat"""
        try:
            # Verificar si existe la tabla antigua
            cursor = old_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_search'")
            if not cursor.fetchone():
                logger.info("Tabla chat_search no encontrada, saltando migración de búsquedas")
                return
            
            # Obtener datos de la tabla antigua
            cursor = old_conn.execute("""
                SELECT chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord, username, name, active
                FROM chat_search
            """)
            
            migrated_count = 0
            for row in cursor.fetchall():
                try:
                    # Insertar en la nueva tabla
                    new_conn.execute("""
                        INSERT INTO product_searches 
                        (chat_id, keywords, category_ids, min_price, max_price, distance, 
                         publish_date, order_by, username, name, active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                        row[8], row[9], row[10], datetime.now(), datetime.now()
                    ))
                    migrated_count += 1
                except Exception as e:
                    logger.error(f"Error migrando búsqueda {row[1]}: {e}")
            
            logger.info(f"Migradas {migrated_count} búsquedas de chat")
            
        except Exception as e:
            logger.error(f"Error en migración de búsquedas: {e}")
    
    def migrate_items(self, old_conn, new_conn):
        """Migra los productos"""
        try:
            # Verificar si existe la tabla antigua
            cursor = old_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item'")
            if not cursor.fetchone():
                logger.info("Tabla item no encontrada, saltando migración de productos")
                return
            
            # Obtener datos de la tabla antigua
            cursor = old_conn.execute("""
                SELECT itemId, chatId, title, price, url, user, publishDate, observaciones
                FROM item
            """)
            
            migrated_count = 0
            for row in cursor.fetchall():
                try:
                    # Insertar en la nueva tabla
                    new_conn.execute("""
                        INSERT INTO products 
                        (item_id, chat_id, title, price, url, user_id, publish_date, 
                         observations, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row[0]), row[1], row[2], row[3], row[4], str(row[5]),
                        row[6], row[7], datetime.now(), datetime.now()
                    ))
                    migrated_count += 1
                except Exception as e:
                    logger.error(f"Error migrando producto {row[0]}: {e}")
            
            logger.info(f"Migrados {migrated_count} productos")
            
        except Exception as e:
            logger.error(f"Error en migración de productos: {e}")
    
    def create_new_database(self):
        """Crea la nueva base de datos con la estructura v2.0"""
        try:
            # Importar aquí para evitar dependencias circulares
            from database import DatabaseManager
            
            # Crear nueva base de datos
            db_manager = DatabaseManager(self.new_db_path)
            logger.info("Nueva base de datos creada con estructura v2.0")
            
        except Exception as e:
            logger.error(f"Error creando nueva base de datos: {e}")
            raise
    
    def migrate(self):
        """Ejecuta la migración completa"""
        logger.info("Iniciando migración de WallBot v1.0 a v2.0")
        
        # Crear backup
        backup_path = self.backup_old_database()
        
        # Crear nueva base de datos
        self.create_new_database()
        
        # Migrar datos si existe la base de datos anterior
        if os.path.exists(self.old_db_path):
            try:
                old_conn = sqlite3.connect(self.old_db_path)
                new_conn = sqlite3.connect(self.new_db_path)
                
                # Migrar búsquedas
                self.migrate_chat_searches(old_conn, new_conn)
                
                # Migrar productos
                self.migrate_items(old_conn, new_conn)
                
                # Commit cambios
                new_conn.commit()
                
                old_conn.close()
                new_conn.close()
                
                logger.info("Migración completada exitosamente")
                
                # Renombrar archivos
                if os.path.exists(self.new_db_path):
                    os.rename(self.old_db_path, f"{self.old_db_path}.v1")
                    os.rename(self.new_db_path, self.old_db_path)
                    logger.info("Base de datos actualizada a v2.0")
                
            except Exception as e:
                logger.error(f"Error durante la migración: {e}")
                if backup_path:
                    logger.info(f"Restaurando backup desde: {backup_path}")
                    shutil.copy2(backup_path, self.old_db_path)
                raise
        else:
            logger.info("No se encontró base de datos anterior, creando nueva")
            # Mover la nueva base de datos a la ubicación correcta
            if os.path.exists(self.new_db_path):
                os.rename(self.new_db_path, self.old_db_path)

def main():
    """Función principal"""
    try:
        # Verificar si estamos en Docker o local
        if os.path.exists("/data"):
            old_db = "/data/db.sqlite"
        else:
            old_db = "db.sqlite"
        
        # Crear directorios si no existen
        os.makedirs("/data", exist_ok=True)
        os.makedirs("/logs", exist_ok=True)
        
        # Ejecutar migración
        migrator = MigrationManager(old_db_path=old_db)
        migrator.migrate()
        
        print("✅ Migración completada exitosamente!")
        print("📝 La base de datos anterior se ha respaldado con extensión .v1")
        print("🚀 WallBot v2.0 está listo para usar")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        print("🔧 Verifica los logs para más detalles")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 