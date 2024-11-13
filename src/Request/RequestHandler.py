import os
from typing import Optional, Dict, List

import requests
from pydantic import BaseModel, ValidationError


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
        # Формируем URL с подстановкой параметров пути
        if path_params:
            endpoint = endpoint.format(**path_params.dict())

        url = f"{self.base_url}/{endpoint}"

        try:
            # Преобразуем параметры запроса в словарь
            query_params_dict = query_params.dict() if query_params else None
            response = requests.get(url, headers=self.headers, params=query_params_dict, timeout=self.timeout)
            response.raise_for_status()

            # Обрабатываем ответ с использованием модели
            data = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
            return response_model.parse_obj(data) if response_model else data
        except requests.exceptions.RequestException as e:
            print(f"Ошибка GET-запроса: {e}")
            return None
        except ValidationError as ve:
            print(f"Ошибка валидации данных ответа: {ve}")
            return None

    def post(
            self, endpoint: str, data: Optional[BaseModel] = None, media_files: Optional[Dict[str, List[str]]] = None,
            response_model: Optional[BaseModel] = None
    ):
        """
        Выполняет POST-запрос к указанному endpoint, включая возможность загрузки файлов.

        :param endpoint: Путь к ресурсу относительно base_url
        :param data: Данные для отправки в формате form-encoded (по умолчанию None)
        :param media_files: Словарь с путями к файлам для загрузки, ключами являются категории ('images', 'videos')
        :param response_model: Модель для валидации данных ответа
        :return: Ответ сервера в формате JSON (если есть) или текстовый ответ
        """
        url = f"{self.base_url}/{endpoint}"
        files = {}

        # Подготовка файлов для отправки
        if media_files:
            for file_type, file_list in media_files.items():
                for file_name in file_list:
                    file_path = os.path.join("media", file_type[:-1],
                                             file_name)  # file_type: images -> img, videos -> video
                    files[file_type] = open(file_path, 'rb')

        try:
            data_dict = data.dict() if data else None
            response = requests.post(url, headers=self.headers, data=data_dict, files=files, timeout=self.timeout)
            response.raise_for_status()

            data = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
            return response_model.parse_obj(data) if response_model else data
        except requests.exceptions.RequestException as e:
            print(f"Ошибка POST-запроса: {e}")
            return None
        except ValidationError as ve:
            print(f"Ошибка валидации данных ответа: {ve}")
            return None
        finally:
            # Закрытие файлов
            for f in files.values():
                f.close()

    def set_headers(self, headers):
        """
        Устанавливает или обновляет заголовки для запросов.

        :param headers: Словарь с заголовками
        """
        self.headers.update(headers)

    def set_timeout(self, timeout):
        """
        Устанавливает тайм-аут для запросов.

        :param timeout: Тайм-аут в секундах
        """
        self.timeout = timeout
