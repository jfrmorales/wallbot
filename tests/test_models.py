"""
Tests para los modelos de datos
"""
import pytest
from pydantic import ValidationError

from models import ProductSearch, Product, SearchResult

class TestProductSearch:
    """Tests para el modelo ProductSearch"""
    
    def test_valid_product_search(self):
        """Test de búsqueda válida"""
        search = ProductSearch(
            chat_id="123456",
            keywords="zapatos rojos",
            min_price=10.0,
            max_price=50.0
        )
        assert search.chat_id == "123456"
        assert search.keywords == "zapatos rojos"
        assert search.min_price == 10.0
        assert search.max_price == 50.0
    
    def test_invalid_price_range(self):
        """Test de rango de precio inválido"""
        with pytest.raises(ValidationError):
            ProductSearch(
                chat_id="123456",
                keywords="zapatos",
                min_price=50.0,
                max_price=10.0  # Precio mínimo mayor que máximo
            )
    
    def test_empty_keywords(self):
        """Test de palabras clave vacías"""
        with pytest.raises(ValidationError):
            ProductSearch(
                chat_id="123456",
                keywords="   "  # Solo espacios
            )

class TestProduct:
    """Tests para el modelo Product"""
    
    def test_valid_product(self):
        """Test de producto válido"""
        product = Product(
            item_id="123",
            chat_id="456",
            title="iPhone 12",
            price=500.0,
            url="iphone-12",
            user_id="789"
        )
        assert product.item_id == "123"
        assert product.title == "iPhone 12"
        assert product.price == 500.0
    
    def test_invalid_price(self):
        """Test de precio inválido"""
        with pytest.raises(ValidationError):
            Product(
                item_id="123",
                chat_id="456",
                title="iPhone 12",
                price=-10.0,  # Precio negativo
                url="iphone-12",
                user_id="789"
            )
    
    def test_empty_title(self):
        """Test de título vacío"""
        with pytest.raises(ValidationError):
            Product(
                item_id="123",
                chat_id="456",
                title="   ",  # Solo espacios
                price=500.0,
                url="iphone-12",
                user_id="789"
            )

class TestSearchResult:
    """Tests para el modelo SearchResult"""
    
    def test_valid_search_result(self):
        """Test de resultado de búsqueda válido"""
        result = SearchResult(
            id="123",
            title="iPhone 12",
            price=500.0,
            web_slug="iphone-12",
            user_id="789"
        )
        assert result.id == "123"
        assert result.title == "iPhone 12"
        assert result.price == 500.0
    
    def test_invalid_price(self):
        """Test de precio inválido en resultado"""
        with pytest.raises(ValidationError):
            SearchResult(
                id="123",
                title="iPhone 12",
                price=0.0,  # Precio cero
                web_slug="iphone-12",
                user_id="789"
            ) 