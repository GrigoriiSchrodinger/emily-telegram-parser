import os
import uuid
import requests
import html2text
import re
from bs4 import BeautifulSoup

class TeleScraperDict:
    def __init__(self, post_url):
        # Инициализация с URL поста и заголовками для запроса
        self.post_url = post_url
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36 TelegramBot (like TwitterBot)'
        }
        self.image_filenames = []  # Список для сохраненных имен файлов изображений
        self.video_filenames = []  # Список для сохраненных имен файлов видео
        self.author = ""  # Автор сообщения
        self.content = ""  # Содержимое сообщения
        self.date_time = ""  # Время публикации сообщения

    @staticmethod
    def html_to_text(html):
        """
        Преобразует HTML в текст, игнорируя ссылки, изображения и форматирование.
        """
        h = html2text.HTML2Text()
        h.body_width = 0
        h.ignore_links = True
        h.ignore_emphasis = True
        h.ignore_images = True
        h.protect_links = True
        h.unicode_snob = True
        h.wrap_links = False
        h.wrap_lists = False
        h.decode_errors = 'ignore'
        text = h.handle(html)
        # Очистка лишних символов форматирования
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'^[ \t]*[\\`]', '', text, flags=re.MULTILINE)
        return text

    def save_media(self, url, media_type):
        folder_name = "media"

        # Создаем папки для медиа, если их нет
        img_folder = os.path.join(folder_name, 'img')
        video_folder = os.path.join(folder_name, 'video')
        os.makedirs(img_folder, exist_ok=True)
        os.makedirs(video_folder, exist_ok=True)

        # Генерация случайного ID для уникальности имени файла
        random_id = uuid.uuid4().hex

        if media_type == 'img':
            file_extension = '.jpg'
            filename = f"img-{random_id}{file_extension}"
            folder = img_folder
        elif media_type == 'vid':
            file_extension = '.mp4'
            filename = f"vid-{random_id}{file_extension}"
            folder = video_folder
        else:
            print(f"Unknown media type: {media_type}")
            return None

        file_path = os.path.join(folder, filename)

        # Если файл существует, возвращаем его имя
        if os.path.exists(file_path):
            print(f"File already exists: {filename}")
            return filename

        # Логируем URL, который будем скачивать
        print(f"Downloading media from {url} to {file_path}")

        try:
            response = requests.get(url)
            response.raise_for_status()  # Проверка статуса ответа
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return filename
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
            return None

    def append_image_urls(self, img_elements):
        base_url = 'https://cdn4.cdn-telegram.org'  # Базовый URL для абсолютных ссылок

        for idx, div in enumerate(img_elements, start=1):
            style = div['style']

            # Ищем все background-image в стиле
            matches = re.findall(r"background-image:url\('(.*?)'\)", style)

            if matches:
                for match in matches:
                    # Если URL относительный, добавляем базовый URL
                    if match.startswith('/'):
                        match = base_url + match
                    image_url = match

                    if image_url:
                        filename = self.save_media(image_url, 'img')
                        if filename:
                            self.image_filenames.append(filename)
                        else:
                            print(f"Failed to download image: {image_url}")  # Логирование ошибки скачивания

    def append_video_urls(self, video_elements, post_id, date_time):
        """
        Извлекает и сохраняет все видео из HTML-элементов.
        """
        for idx, video in enumerate(video_elements, start=1):
            video_tag = video.find('video')  # Извлекаем URL через тег <video>
            if video_tag:
                src = video_tag.get('src')
                if src:
                    filename = self.save_media(src, 'vid')
                    if filename:
                        self.video_filenames.append(filename)

    async def fetch_data(self):
        """
        Скачивает данные с поста по его URL.
        """
        url = self.post_url + '?embed=1&mode=tme'
        try:
            # Запрос и парсинг HTML с использованием BeautifulSoup
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            link_html = BeautifulSoup(response.text, 'html.parser')

            # Извлечение текста сообщения
            self.content = self.html_to_text(
                str(link_html.find('div', {'class': 'tgme_widget_message_text js-message_text', 'dir': 'auto'})))
            self.author = self.html_to_text(
                str(link_html.find('div', {'class': 'tgme_widget_message_author accent_color'}).find('a', {
                    'class': 'tgme_widget_message_owner_name'}).find('span', {'dir': 'auto'})))
            self.date_time = self.html_to_text(
                str(link_html.find('span', {'class': 'tgme_widget_message_meta'}).find('time', {'class': 'datetime'})))

            # Извлечение ID поста
            post_id = self.post_url.split('/')[-1]

            # Обработка изображений и видео
            img_elements = link_html.findAll('a', {'class': 'tgme_widget_message_photo_wrap'})
            if img_elements:
                self.append_image_urls(img_elements)

            video_elements = link_html.findAll('div', {'class': 'tgme_widget_message_video_wrap'})
            if video_elements:
                self.append_video_urls(video_elements, post_id, self.date_time)

        except requests.exceptions.RequestException as err:
            print(f"Request failed: {err}")

    async def get(self):
        """
        Асинхронно получает данные и возвращает их в виде словаря.
        """
        await self.fetch_data()
        return {
            "author": self.author,
            "content": self.content,
            "date_time": self.date_time,
            "images": self.image_filenames,
            "videos": self.video_filenames
        }