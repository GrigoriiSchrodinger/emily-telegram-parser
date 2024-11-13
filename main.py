import asyncio
import re
import time
from datetime import datetime
from io import BytesIO
from typing import Any, Optional, List

import requests
from fastapi import UploadFile

from src.conf import api
from src.feature.TeleParser import TeleScraperDict
from src.feature.TelegramParser import TelegramLastNews
from src.request.schemas import NewsExistsResponseModel, NewsExistsRequestModel, NewPostResponseModel, \
    NewPostRequestModel


def extract_channel_and_post_id(url: str) -> tuple[str | Any, ...] | tuple[None, None]:
    match = re.search(r'https://t\.me/s/([^/]+)/(\d+)', url)
    return match.groups() if match else (None, None)


def get_news(channel: str, id_post: int) -> NewsExistsResponseModel:
    params = NewsExistsRequestModel(channel=channel, id_post=id_post)
    return api.get("exists/{channel}/{id_post}", path_params=params, response_model=NewsExistsResponseModel)


def create_news(channel: str, id_post: int, timestamp: datetime, url: str, images: Optional[List[UploadFile]] = None, videos: Optional[List[UploadFile] ] = None) -> None:
    files = []

    # Добавляем изображения и видео к файлам
    for img in images:
        files.append(('images', (img.filename, img.file, 'image/jpeg')))
    for vid in videos:
        files.append(('videos', (vid.filename, vid.file, 'video/mp4')))

    data = {
        'channel': channel,
        'id_post': id_post,
        'time': timestamp.isoformat(),
        'url': url
    }

    response = requests.post("http://0.0.0.0:8000/news/create", files=files, data=data)

    # Обработка ответа
    if response.status_code == 200:
        print("Запрос успешно отправлен!")
    else:
        print(f"Ошибка POST-запроса: {response.status_code}, ответ: {response.text}")

def create_upload_file(filename):
    # Открываем файл и создаем UploadFile
    with open(filename, "rb") as file:
        return UploadFile(filename=filename, file=BytesIO(file.read()))


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
                    print(result)
                    images = [create_upload_file(f"media/img/{image}") for image in result["images"]]
                    videos = [create_upload_file(f"media/video/{video}") for video in result["videos"]]
                    create_news(channel=channel_name, id_post=int(post_id), timestamp=news["date"], url=news["url"], images=images, videos=videos)


if __name__ == '__main__':
    while True:
        get_telegram_news()
        time.sleep(360)