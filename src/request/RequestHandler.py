from typing import Optional

import requests
from pydantic import BaseModel, ValidationError
from src.logger import logger


class RequestHandler:
    def __init__(self, base_url, headers=None, timeout=10):
        """
        Инициализация класса для работы с запросами.

        :param base_url: Базовый URL для запросов
        :param headers: Заголовки для запросов (по умолчанию None)
        :param timeout: Тайм-аут для запросов (по умолчанию 10 секунд)
        """
        self.base_url = base_url
        self.headers = headers if headers is not None else {}
        self.timeout = timeout
        logger.debug("Инициализация RequestHandler", extra={"tags": {
            "base_url": base_url,
            "timeout": timeout
        }})

    def get(
            self, endpoint: str, path_params: Optional[BaseModel] = None, query_params: Optional[BaseModel] = None,
            response_model: Optional[BaseModel] = None
    ):
        """
        Выполняет GET-запрос к указанному endpoint.

        :param query_params:
        :param path_params:
        :param response_model:
        :param endpoint: Путь к ресурсу относительно base_url
        :return: Ответ сервера в формате JSON (если есть) или текстовый ответ
        """
        try:
            # Логирование параметров запроса
            logger.info("Начало GET-запроса", extra={"tags": {
                "operation": "http_request",
                "endpoint": endpoint,
                "path_params": path_params.dict() if path_params else None,
                "query_params": query_params.dict() if query_params else None
            }})
            
            # Формируем URL с подстановкой параметров пути
            if path_params:
                endpoint = endpoint.format(**path_params.dict())

            url = f"{self.base_url}/{endpoint}"

            # Преобразуем параметры запроса в словарь
            query_params_dict = query_params.dict() if query_params else None
            response = requests.get(url, headers=self.headers, params=query_params_dict, timeout=self.timeout)
            response.raise_for_status()

            # Логирование успешного ответа
            logger.debug("Успешный GET-ответ", extra={"tags": {
                "operation": "http_response",
                "status_code": response.status_code,
                "url": response.url,
                "response_size": len(response.content)
            }})
            
            # Обрабатываем ответ с использованием модели
            data = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
            if response_model:
                parsed_data = response_model.parse_obj(data)
                logger.info("Данные успешно валидированы", extra={"tags": {
                    "model": response_model.__name__,
                    "data_size": len(str(parsed_data))
                }})
                return parsed_data
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка сетевого запроса", extra={"tags": {
                "error_type": type(e).__name__,
                "url": url,
                "method": "GET"
            }}, exc_info=True)
            return None
        except ValidationError as ve:
            logger.error("Ошибка валидации ответа", extra={"tags": {
                "model": response_model.__name__ if response_model else "None",
                "errors": ve.errors()
            }}, exc_info=True)
            return None

    def post_files(self, path_params: Optional[BaseModel], endpoint: str, files: list) -> dict:
        try:
            logger.info("Начало загрузки файлов", extra={"tags": {
                "operation": "file_upload",
                "endpoint": endpoint,
                "file_count": len(files)
            }})
            
            if path_params:
                endpoint = endpoint.format(**path_params.dict())
            # query_params_dict = query_params.dict() if query_params else None
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(url, files=files)
            response.raise_for_status()
            
            logger.info("Файлы успешно загружены", extra={"tags": {
                "status_code": response.status_code,
                "upload_time": response.elapsed.total_seconds()
            }})
            return response.json()
            
        except Exception as e:
            logger.error("Ошибка загрузки файлов", extra={"tags": {
                "error_type": type(e).__name__,
                "url": url,
                "file_count": len(files)
            }}, exc_info=True)
            return {}

    def post(self, endpoint: str, data: Optional[BaseModel] = None, response_model: Optional[BaseModel] = None):
        """
            Выполняет POST-запрос к указанному endpoint.

            :param self:
            :param response_model:
            :param endpoint: Путь к ресурсу относительно base_url
            :param data: Данные для отправки в формате form-encoded (по умолчанию None)
            :return: Ответ сервера в формате JSON (если есть) или текстовый ответ
            """
        try:
            logger.info("Начало POST-запроса", extra={"tags": {
                "operation": "http_request",
                "endpoint": endpoint,
                "data_size": len(str(data.dict())) if data else 0
            }})
            
            url = f"{self.base_url}/{endpoint}"
            data_dict = data.dict() if data else None
            
            response = requests.post(url, headers=self.headers, json=data_dict, timeout=self.timeout)
            response.raise_for_status()
            
            logger.debug("Успешный POST-ответ", extra={"tags": {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }})
            
            response_data = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
            if response_model:
                parsed_data = response_model.parse_obj(response_data)
                logger.info("POST-данные валидированы", extra={"tags": {
                    "model": response_model.__name__,
                    "data_size": len(str(parsed_data))
                }})
                return parsed_data
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка сетевого запроса", extra={"tags": {
                "error_type": type(e).__name__,
                "url": url,
                "method": "POST"
            }}, exc_info=True)
            return None
        except ValidationError as ve:
            logger.error("Ошибка валидации ответа", extra={"tags": {
                "model": response_model.__name__ if response_model else "None",
                "errors": ve.errors()
            }}, exc_info=True)
            return None


def set_headers(self, headers):
    """
    Устанавливает или обновляет заголовки для запросов.

    :param self:
    :param headers: Словарь с заголовками
    """
    old_headers = self.headers.copy()
    self.headers.update(headers)
    logger.info("Обновление заголовков", extra={"tags": {
        "added_headers": list(headers.keys()),
        "total_headers": len(self.headers)
    }})


def set_timeout(self, timeout):
    """
    Устанавливает тайм-аут для запросов.

    :param self:
    :param timeout: Тайм-аут в секундах
    """
    old_timeout = self.timeout
    self.timeout = timeout
    logger.debug("Изменение таймаута", extra={"tags": {
        "old_timeout": old_timeout,
        "new_timeout": timeout
    }})