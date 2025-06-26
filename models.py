"""
Modelos de datos para el bot de seguimiento de productos
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import locale

class ProductSearch(BaseModel):
    """Modelo para búsquedas de productos"""
    chat_id: str
    keywords: str = Field(..., min_length=1, max_length=200)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    category_ids: Optional[str] = None
    distance: str = "400"
    publish_date: int = 24
    order: str = "newest"
    username: Optional[str] = None
    name: Optional[str] = None
    active: bool = True
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        """Valida que las palabras clave no estén vacías"""
        if not v.strip():
            raise ValueError('Las palabras clave no pueden estar vacías')
        return v.strip()
    
    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v, info):
        """Valida que el precio máximo sea mayor que el mínimo"""
        if v is not None and info.data and 'min_price' in info.data and info.data['min_price'] is not None:
            if v <= info.data['min_price']:
                raise ValueError('El precio máximo debe ser mayor que el precio mínimo')
        return v

class Product(BaseModel):
    """Modelo para productos encontrados"""
    item_id: str
    chat_id: str
    title: str
    price: float
    url: str
    user_id: str
    publish_date: Optional[int] = None
    observations: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Valida que el precio sea positivo"""
        if v <= 0:
            raise ValueError('El precio debe ser positivo')
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Valida que el título no esté vacío"""
        if not v.strip():
            raise ValueError('El título no puede estar vacío')
        return v.strip()

class Notification(BaseModel):
    """Modelo para notificaciones"""
    chat_id: str
    message: str
    product_id: str
    notification_type: str  # 'new_product', 'price_drop'
    created_at: datetime = Field(default_factory=datetime.now)

class SearchResult(BaseModel):
    """Modelo para resultados de búsqueda de Wallapop"""
    id: str
    title: str
    price: float
    web_slug: str
    user_id: str
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Valida que el precio sea positivo"""
        if v <= 0:
            raise ValueError('El precio debe ser positivo')
        return v 