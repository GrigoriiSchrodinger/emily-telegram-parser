import os
import uuid
import requests
import html2text
import re
from bs4 import BeautifulSoup
import time

class TeleScraperDict:
    def __init__(self, post_url):
        self.post_url = post_url
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36 TelegramBot (like TwitterBot)'
        }
        self.image_filenames = []  # Список для сохраненных имен файлов изображений
        self.video_filenames = []  # Список для сохраненных имен файлов видео
        self.author = ""  # Автор сообщения
        self.content = ""  # Содержимое сообщения
        self.date_time = ""  # Время публикации сообщения
        self.media_download_delay = 1  # Добавляем задержку в секундах между загрузками
        self.max_retries = 3  # Максимальное количество попыток скачивания
        self.retry_delay = 2  # Задержка между попытками в секундах

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

        print(f"Downloading media from {url} to {file_path}")

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                time.sleep(self.media_download_delay)
                return filename
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed to download {url}: {e}")
                if attempt < self.max_retries - 1:
                    print(f"Waiting {self.retry_delay} seconds before retry...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"All attempts to download {url} failed")
                    return None

    def append_image_urls(self, img_elements):
        base_url = 'https://cdn4.cdn-telegram.org'
        post_id = self.post_url.split('/')[-1]

        for idx, div in enumerate(img_elements, start=1):
            parent_msg = div.find_parent('div', {'class': 'tgme_widget_message'})
            if parent_msg and parent_msg.get('data-post', '').endswith(post_id):
                style = div['style']
                matches = re.findall(r"background-image:url\('(.*?)'\)", style)

                if matches:
                    for match in matches:
                        if match.startswith('/'):
                            match = base_url + match
                        image_url = match

                        if image_url:
                            filename = self.save_media(image_url, 'img')
                            if filename:
                                self.image_filenames.append(filename)
                            else:
                                print(f"Failed to download image: {image_url}")

    def append_video_urls(self, video_elements, post_id, date_time):
        """
        Извлекает и сохраняет все видео из HTML-элементов.
        """
        for idx, video in enumerate(video_elements, start=1):
            parent_msg = video.find_parent('div', {'class': 'tgme_widget_message'})
            if parent_msg and parent_msg.get('data-post', '').endswith(post_id):
                video_tag = video.find('video')
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
            # Запрос и парсинг HTML
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