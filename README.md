# WallBot - Bot de Seguimiento de Productos

![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/z0r3f/wallbot-docker) [![Docker pulls](https://img.shields.io/docker/pulls/z0r3f/wallbot-docker?style=flat-square)](https://hub.docker.com/r/z0r3f/wallbot-docker)  [![commit_freq](https://img.shields.io/github/commit-activity/m/z0r3f/wallbot?style=flat-square)](https://github.com/z0r3f/wallbot/commits) [![Build Status](https://travis-ci.com/z0r3f/wallbot.svg)](https://travis-ci.com/z0r3f/wallbot)  [![last_commit](https://img.shields.io/github/last-commit/z0r3f/wallbot?style=flat-square)](https://github.com/z0r3f/wallbot/commits) ![Docker Image Version (latest by date)](https://img.shields.io/docker/v/z0r3f/wallbot-docker) ![GitHub](https://img.shields.io/github/license/z0r3f/wallbot)

## 🎯 Descripción

WallBot es un bot de Telegram inteligente para el seguimiento de productos en Wallapop. Te permite configurar búsquedas personalizadas y recibir notificaciones automáticas cuando:

- 🆕 Se publican nuevos productos que coinciden con tus criterios
- 💥 Los productos que sigues bajan de precio
- 📊 Mantener un historial de productos y precios

## ✨ Características

- **Búsquedas personalizadas**: Define palabras clave, rangos de precio y categorías
- **Notificaciones inteligentes**: Recibe alertas solo de productos relevantes
- **Seguimiento de precios**: Detecta automáticamente bajadas de precio
- **Interfaz intuitiva**: Comandos simples y mensajes claros
- **Arquitectura modular**: Código limpio y mantenible
- **Configuración flexible**: Variables de entorno para personalización

## 🚀 Instalación

### Requisitos

- Python 3.8+
- Token de bot de Telegram
- Acceso a internet

### Instalación local

1. **Clonar el repositorio**
```bash
git clone https://github.com/z0r3f/wallbot.git
cd wallbot
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
cp env.example .env
# Editar .env con tu configuración
```

4. **Ejecutar el bot**
```bash
python main.py
```

### Docker

```bash
# Construir imagen
docker build --tag wallbot:latest .

# Ejecutar contenedor
docker run --env BOT_TOKEN=<YOUR-TOKEN> wallbot:latest
```

## 📋 Uso

### Comandos disponibles

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/start` o `/help` | Muestra ayuda | `/start` |
| `/add producto,min-max` | Añadir búsqueda | `/add zapatos rojos,10-50` |
| `/del producto` | Eliminar búsqueda | `/del zapatos rojos` |
| `/list` | Ver búsquedas activas | `/list` |
| `/stats` | Estadísticas del bot | `/stats` |

### Búsquedas rápidas

También puedes enviar directamente el nombre del producto:
```
zapatos rojos
```
Esto añadirá automáticamente una búsqueda sin filtros de precio.

### Ejemplos de uso

1. **Buscar productos con rango de precio**
```
/add iPhone 12,200-400
```

2. **Buscar productos sin límite de precio**
```
/add bicicleta
```

3. **Ver tus búsquedas activas**
```
/list
```

## ⚙️ Configuración

### Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `BOT_TOKEN` | Token del bot de Telegram | Requerido |
| `DATABASE_PATH` | Ruta de la base de datos | `/data/db.sqlite` |
| `SEARCH_INTERVAL` | Intervalo de búsqueda (segundos) | `300` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `LOG_FILE` | Archivo de log | `/logs/wallbot.log` |
| `MAX_NOTIFICATIONS_PER_HOUR` | Límite de notificaciones | `50` |
| `ITEM_CLEANUP_HOURS` | Horas para limpiar productos | `24` |

## 🏗️ Arquitectura

El bot está diseñado con una arquitectura modular:

```
wallbot/
├── main.py                 # Punto de entrada
├── bot.py                  # Bot principal de Telegram
├── product_tracker.py      # Servicio de seguimiento
├── wallapop_client.py      # Cliente de API de Wallapop
├── notification_service.py # Servicio de notificaciones
├── database.py            # Gestor de base de datos
├── models.py              # Modelos de datos
├── config.py              # Configuración centralizada
└── requirements.txt       # Dependencias
```

### Componentes principales

- **ProductTracker**: Coordina el seguimiento de productos
- **WallapopClient**: Interactúa con la API de Wallapop
- **NotificationService**: Maneja notificaciones de Telegram
- **DatabaseManager**: Gestiona la persistencia de datos
- **Models**: Define la estructura de datos con validación

## 🔧 Desarrollo

### Estructura del proyecto

```
wallbot/
├── src/                   # Código fuente
├── tests/                 # Tests unitarios
├── logs/                  # Archivos de log
├── data/                  # Base de datos
├── docker/                # Archivos Docker
└── docs/                  # Documentación
```

### Ejecutar tests

```bash
python -m pytest tests/
```

### Formatear código

```bash
black .
isort .
```

## 📊 Monitoreo

El bot incluye:

- **Logging detallado**: Registro de todas las operaciones
- **Estadísticas**: Métricas de uso y rendimiento
- **Manejo de errores**: Recuperación automática de fallos
- **Rate limiting**: Protección contra spam

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas o preguntas:

1. Revisa la documentación
2. Busca en los issues existentes
3. Crea un nuevo issue con detalles del problema

## 🔄 Changelog

### v2.0.0 (Refactorización completa)
- ✅ Arquitectura modular y escalable
- ✅ Mejor manejo de errores y validaciones
- ✅ Sistema de notificaciones mejorado
- ✅ Base de datos optimizada
- ✅ Configuración centralizada
- ✅ Logging detallado
- ✅ Tests unitarios
- ✅ Documentación completa

### v1.0.0 (Versión original)
- ✅ Funcionalidad básica de seguimiento
- ✅ Notificaciones de Telegram
- ✅ Búsquedas en Wallapop