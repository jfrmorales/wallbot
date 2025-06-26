"""
Cliente para interactuar con la API de Wallapop
"""
import requests
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus
from fake_useragent import UserAgent
import time
import asyncio
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from models import ProductSearch, SearchResult
from config import Config

logger = logging.getLogger(__name__)

class WallapopAPIError(Exception):
    """Excepción personalizada para errores de la API de Wallapop"""
    pass

class WallapopClient:
    """Cliente para la API de Wallapop"""
    
    def __init__(self):
        self.base_url = Config.WALLAPOP_API_URL
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configura la sesión HTTP con headers apropiados"""
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es,ru;q=0.9,en;q=0.8,de;q=0.7,pt;q=0.6',
            'Connection': 'keep-alive',
            'DeviceOS': '0',
            'Origin': 'https://es.wallapop.com',
            'Referer': 'https://es.wallapop.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-AppVersion': '75491',
            'X-DeviceOS': '0',
            'sec-ch-ua-mobile': '?0',
        })
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers actualizados para la petición"""
        headers = self.session.headers.copy()
        # User-Agent realista de Chrome en Windows
        headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/125.0.0.0 Safari/537.36'
        )
        headers['Accept-Language'] = 'es-ES,es;q=0.9,en;q=0.8'
        headers['Referer'] = 'https://es.wallapop.com/'
        headers['Origin'] = 'https://es.wallapop.com'
        return headers
    
    def _build_search_url(self, search: ProductSearch) -> str:
        """Construye la URL de búsqueda basada en los parámetros"""
        params = []
        
        # Palabras clave
        keywords = quote_plus(search.keywords)
        params.append(f"keywords={keywords}")
        
        # Filtro de tiempo
        params.append("time_filter=today")
        
        # Precio mínimo
        if search.min_price is not None:
            params.append(f"min_sale_price={search.min_price}")
        
        # Precio máximo
        if search.max_price is not None:
            params.append(f"max_sale_price={search.max_price}")
        
        # Categorías
        if search.category_ids:
            params.append(f"category_ids={search.category_ids}")
        
        # Distancia
        if search.distance:
            params.append(f"dist={search.distance}")
        
        # Orden
        if search.order:
            params.append(f"order_by={search.order}")
        
        return f"{self.base_url}?{'&'.join(params)}"
    
    def search_products(self, search: ProductSearch) -> List[SearchResult]:
        """
        Busca productos en Wallapop según los criterios especificados
        
        Args:
            search: Objeto ProductSearch con los criterios de búsqueda
            
        Returns:
            Lista de SearchResult con los productos encontrados
            
        Raises:
            WallapopAPIError: Si hay un error en la API
        """
        try:
            url = self._build_search_url(search)
            logger.info(f"Buscando productos: {url}")
            
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise WallapopAPIError(f"Error HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            search_objects = data.get('search_objects', [])
            
            results = []
            for item in search_objects:
                try:
                    search_result = SearchResult(
                        id=str(item['id']),
                        title=item['title'],
                        price=float(item['price']),
                        web_slug=item['web_slug'],
                        user_id=str(item['user']['id'])
                    )
                    results.append(search_result)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error al procesar item {item.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Encontrados {len(results)} productos para búsqueda: {search.keywords}")
            if results:
                for r in results[:3]:  # Muestra hasta 3 productos como ejemplo
                    logger.info(f"Ejemplo producto: id={r.id}, título='{r.title}', precio={r.price}€, usuario={r.user_id}")
            else:
                logger.info(f"Respuesta sin productos para '{search.keywords}': {data}")
            return results
            
        except requests.RequestException as e:
            logger.error(f"Error de red al buscar productos: {e}")
            raise WallapopAPIError(f"Error de red: {e}")
        except Exception as e:
            logger.error(f"Error inesperado al buscar productos: {e}")
            raise WallapopAPIError(f"Error inesperado: {e}")
    
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalles completos de un producto específico
        
        Args:
            product_id: ID del producto
            
        Returns:
            Diccionario con los detalles del producto o None si no se encuentra
        """
        try:
            url = f"https://api.wallapop.com/api/v3/items/{product_id}"
            headers = self._get_headers()
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Producto no encontrado: {product_id}")
                return None
            else:
                logger.error(f"Error al obtener detalles del producto {product_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error al obtener detalles del producto {product_id}: {e}")
            return None
    
    def search_multiple(self, searches: List[ProductSearch]) -> Dict[str, List[SearchResult]]:
        """
        Realiza múltiples búsquedas en paralelo
        
        Args:
            searches: Lista de búsquedas a realizar
            
        Returns:
            Diccionario con los resultados de cada búsqueda
        """
        results = {}
        
        for search in searches:
            try:
                search_results = self.search_products(search)
                results[f"{search.chat_id}_{search.keywords}"] = search_results
                
                # Pequeña pausa para no sobrecargar la API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error en búsqueda {search.keywords}: {e}")
                results[f"{search.chat_id}_{search.keywords}"] = []
        
        return results
    
    def search_products_playwright(self, search: ProductSearch) -> List[SearchResult]:
        """
        Alternativa: Busca productos usando Playwright para simular un navegador real.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright no está instalado. Instálalo con 'pip install playwright' y ejecuta 'playwright install'.")
            return []
        url = self._build_search_url(search)
        logger.info(f"[Playwright] Buscando productos: {url}")
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Interceptar la respuesta de la API
                api_response = None
                def handle_response(response):
                    nonlocal api_response
                    if "api/v3/general/search" in response.url:
                        api_response = response
                
                page.on("response", handle_response)
                
                # Navegar a la página principal de Wallapop
                page.goto("https://es.wallapop.com/", wait_until="networkidle")
                
                # Hacer la petición a la API
                response = page.goto(url, wait_until="networkidle")
                
                if api_response and api_response.status == 200:
                    try:
                        data = api_response.json()
                        search_objects = data.get('search_objects', [])
                        for item in search_objects:
                            try:
                                search_result = SearchResult(
                                    id=str(item['id']),
                                    title=item['title'],
                                    price=float(item['price']),
                                    web_slug=item['web_slug'],
                                    user_id=str(item['user']['id'])
                                )
                                results.append(search_result)
                            except (KeyError, ValueError) as e:
                                logger.warning(f"[Playwright] Error al procesar item {item.get('id', 'unknown')}: {e}")
                                continue
                        logger.info(f"[Playwright] Encontrados {len(results)} productos para búsqueda: {search.keywords}")
                        if results:
                            for r in results[:3]:
                                logger.info(f"[Playwright] Ejemplo producto: id={r.id}, título='{r.title}', precio={r.price}€, usuario={r.user_id}")
                        else:
                            logger.info(f"[Playwright] Respuesta sin productos para '{search.keywords}': {data}")
                    except Exception as e:
                        logger.error(f"[Playwright] Error parseando JSON: {e}")
                        logger.info(f"[Playwright] Contenido de respuesta: {api_response.text()[:500]}")
                else:
                    logger.error(f"[Playwright] Error en respuesta: status={response.status if response else 'None'}")
                    if response:
                        logger.info(f"[Playwright] Contenido de respuesta: {response.text()[:500]}")
                
                browser.close()
        except Exception as e:
            logger.error(f"[Playwright] Error inesperado al buscar productos: {e}")
        return results
    
    def search_products_playwright_with_cookies(self, search: ProductSearch, cookies: str = None, proxy: str = None) -> List[SearchResult]:
        """
        Busca productos usando Playwright con cookies de sesión reales y opcionalmente un proxy.
        Las cookies deben obtenerse del navegador después de iniciar sesión en Wallapop.
        El proxy debe ser una URL tipo 'http://usuario:pass@host:puerto' o 'socks5://...'.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright no está instalado. Instálalo con 'pip install playwright' y ejecuta 'playwright install'.")
            return []
        
        url = self._build_search_url(search)
        logger.info(f"[Playwright+Cookies+Proxy] Buscando productos: {url} (proxy={proxy})")
        results = []
        
        try:
            launch_args = {}
            if proxy:
                launch_args['proxy'] = { 'server': proxy }
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, **launch_args)
                context = browser.new_context()
                
                # Añadir cookies si se proporcionan
                if cookies:
                    try:
                        # Parsear cookies del formato "name=value; name2=value2"
                        cookie_list = []
                        for cookie_str in cookies.split(';'):
                            if '=' in cookie_str:
                                name, value = cookie_str.strip().split('=', 1)
                                cookie_list.append({
                                    'name': name.strip(),
                                    'value': value.strip(),
                                    'domain': '.wallapop.com',
                                    'path': '/'
                                })
                        context.add_cookies(cookie_list)
                        logger.info(f"[Playwright+Cookies+Proxy] Añadidas {len(cookie_list)} cookies")
                    except Exception as e:
                        logger.warning(f"[Playwright+Cookies+Proxy] Error añadiendo cookies: {e}")
                
                page = context.new_page()
                
                # Interceptar la respuesta de la API
                api_response = None
                def handle_response(response):
                    nonlocal api_response
                    if "api/v3/general/search" in response.url:
                        api_response = response
                
                page.on("response", handle_response)
                
                # Navegar a la página principal de Wallapop
                page.goto("https://es.wallapop.com/", wait_until="networkidle")
                
                # Hacer la petición a la API
                response = page.goto(url, wait_until="networkidle")
                
                if api_response and api_response.status == 200:
                    try:
                        data = api_response.json()
                        search_objects = data.get('search_objects', [])
                        for item in search_objects:
                            try:
                                search_result = SearchResult(
                                    id=str(item['id']),
                                    title=item['title'],
                                    price=float(item['price']),
                                    web_slug=item['web_slug'],
                                    user_id=str(item['user']['id'])
                                )
                                results.append(search_result)
                            except (KeyError, ValueError) as e:
                                logger.warning(f"[Playwright+Cookies+Proxy] Error al procesar item {item.get('id', 'unknown')}: {e}")
                                continue
                        logger.info(f"[Playwright+Cookies+Proxy] Encontrados {len(results)} productos para búsqueda: {search.keywords}")
                        if results:
                            for r in results[:3]:
                                logger.info(f"[Playwright+Cookies+Proxy] Ejemplo producto: id={r.id}, título='{r.title}', precio={r.price}€, usuario={r.user_id}")
                        else:
                            logger.info(f"[Playwright+Cookies+Proxy] Respuesta sin productos para '{search.keywords}': {data}")
                    except Exception as e:
                        logger.error(f"[Playwright+Cookies+Proxy] Error parseando JSON: {e}")
                        logger.info(f"[Playwright+Cookies+Proxy] Contenido de respuesta: {api_response.text()[:500]}")
                else:
                    logger.error(f"[Playwright+Cookies+Proxy] Error en respuesta: status={response.status if response else 'None'}")
                    if response:
                        logger.info(f"[Playwright+Cookies+Proxy] Contenido de respuesta: {response.text()[:500]}")
                
                browser.close()
        except Exception as e:
            logger.error(f"[Playwright+Cookies+Proxy] Error inesperado al buscar productos: {e}")
        return results 