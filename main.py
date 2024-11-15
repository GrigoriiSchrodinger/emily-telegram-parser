import asyncio
import os
import re
import time
from typing import Any

from src.conf import api
from src.feature.TeleParser import TeleScraperDict
from src.feature.TelegramParser import TelegramLastNews
from src.request.schemas import NewsExistsResponseModel, NewsExistsRequestModel, NewPostResponseModel, \
    NewPostRequestModel, UploadMediaPathParams


def extract_channel_and_post_id(url: str) -> tuple[str | Any, ...] | tuple[None, None]:
    match = re.search(r'https://t\.me/s/([^/]+)/(\d+)', url)
    return match.groups() if match else (None, None)


def get_news(channel: str, id_post: int) -> NewsExistsResponseModel:
    params = NewsExistsRequestModel(channel=channel, id_post=id_post)
    return api.get("exists/{channel}/{id_post}", path_params=params, response_model=NewsExistsResponseModel)


def create_news(channel: str, id_post: int, text: str, timestamp: str, url: str) -> None:
    data = NewPostRequestModel(channel=channel, id_post=id_post, text=text, time=timestamp, url=url)
    api.post("create", data=data, response_model=NewPostResponseModel)


async def upload_media_files(id_post: int, channel: str, images: list[str], videos: list[str]) -> dict:
    files = []

    try:
        # Подготовка файлов для отправки
        for image in images:
            # Добавляем префикс пути к изображениям
            image_path = os.path.join('media', 'img', image)
            if os.path.exists(image_path):
                files.append(('files', ('image.jpg', open(image_path, 'rb'), 'image/jpeg')))
            else:
                print(f"Файл изображения не найден: {image_path}")

        for video in videos:
            # Добавляем префикс пути к видео
            video_path = os.path.join('media', 'video', video)
            if os.path.exists(video_path):
                files.append(('files', ('video.mp4', open(video_path, 'rb'), 'video/mp4')))
            else:
                print(f"Видео файл не найден: {video_path}")

        if not files:
            print("Нет файлов для загрузки")
            return {}

        path_params = UploadMediaPathParams(id_post=id_post, channel=channel)
        response = api.post_files(
            endpoint="upload-media/{id_post}/{channel}",
            path_params=path_params,
            files=files
        )
        return response
    finally:
        # Закрываем все открытые файлы
        for file_tuple in files:
            try:
                file_tuple[1][1].close()
            except:
                pass

def get_telegram_news():
    channels = ["netstalkers", "omanko"]
    parser = TelegramLastNews()
    for channel in channels:
        last_news = parser.get(channel)
        for news in last_news:
            channel_name, post_id = extract_channel_and_post_id(news["url"])
            if channel_name and post_id:
                if not get_news(channel=channel_name, id_post=int(post_id)).exists:
                    scraper = TeleScraperDict(news["url"])
                    result = asyncio.run(scraper.get())
                    create_news(channel=channel_name, id_post=int(post_id), timestamp=news["date"], url=news["url"], text=news["content"])
                    if result.get('images') or result.get('videos'):
                        asyncio.run(upload_media_files(
                            images=result.get('images', []),
                            videos=result.get('videos', []),
                            id_post=post_id,
                            channel=channel
                        ))

if __name__ == '__main__':
    while True:
        get_telegram_news()
        time.sleep(360)
