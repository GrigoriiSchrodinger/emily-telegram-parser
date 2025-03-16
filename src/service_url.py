from enum import Enum
from typing import Dict, Optional

from src.conf import ENV


class Environment(str, Enum):
    LOCALHOST = "localhost"
    PRODUCTION = "production"


SERVICE_URLS: Dict[str, Dict[str, str]] = {
    Environment.LOCALHOST: {
        "emily_database_handler": "http://localhost:8000",
        "redis": "localhost",
        "loki": "http://localhost:3100"
    },
    Environment.PRODUCTION: {
        "emily_database_handler": "http://emily-database-handler:8000",
        "redis": "redis",
        "loki": "http://loki:3100"
    }
}


def get_service_url(service_name: str) -> Optional[str]:
    """
    Получает URL сервиса по его имени для текущего окружения.
    
    Args:
        service_name: Имя сервиса
        
    Returns:
        URL сервиса или None, если сервис не найден
    
    Raises:
        KeyError: Если текущее окружение не поддерживается
    """
    if ENV not in SERVICE_URLS:
        raise KeyError(f"Неизвестное окружение: {ENV}. Поддерживаемые окружения: {list(SERVICE_URLS.keys())}")

    return SERVICE_URLS[ENV].get(service_name)


def get_url_emily_database_handler() -> str:
    """Возвращает URL для сервиса emily_database_handler."""
    return get_service_url("emily_database_handler") or SERVICE_URLS[Environment.LOCALHOST]["emily_database_handler"]


def get_url_redis() -> str:
    """Возвращает URL для сервиса redis."""
    return get_service_url("redis") or SERVICE_URLS[Environment.LOCALHOST]["redis"]


def get_url_loki() -> str:
    """Возвращает URL для сервиса loki."""
    return get_service_url("loki") or SERVICE_URLS[Environment.LOCALHOST]["loki"]
