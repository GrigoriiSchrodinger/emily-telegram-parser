import json
import re
import time
from datetime import datetime
from typing import Any

from src.request.schemas import (
    NewsExistsResponseModel,
    NewsExistsRequestModel,
    NewPostRequestModel,
    NewPostResponseModel
)
from src.conf import api, redis
from src.feature.TelegramParser import TelegramLastNews


def extract_channel_and_post_id(url: str) -> tuple[str | Any, ...] | tuple[None, None]:
    match = re.search(r'https://t\.me/s/([^/]+)/(\d+)', url)
    return match.groups() if match else (None, None)


def get_news(channel: str, id_post: int) -> NewsExistsResponseModel:
    params = NewsExistsRequestModel(channel=channel, id_post=id_post)
    return api.get("exists/{channel}/{id_post}", path_params=params, response_model=NewsExistsResponseModel)


def create_news(channel: str, id_post: int, timestamp: datetime, url: str) -> None:
    data = NewPostRequestModel(channel=channel, id_post=id_post, time=timestamp, url=url)
    api.post("create", data=data, response_model=NewPostResponseModel)


def get_telegram_news():
    channels = ["netstalkers", "omanko", "exploitex", "nogirlshere"]
    parser = TelegramLastNews()
    for channel in channels:
        last_news = parser.get(channel)
        for news in last_news:
            channel_name, post_id = extract_channel_and_post_id(news["url"])
            if channel_name and post_id:
                if not get_news(channel=channel_name, id_post=int(post_id)).exists:
                    create_news(channel=channel_name, id_post=int(post_id), timestamp=news["date"], url=news["url"])
                    json_news = {"channel": channel_name, "content": news["content"]}
                    redis.send_to_queue(json.dumps(json_news))


if __name__ == '__main__':
    while True:
        get_telegram_news()
        time.sleep(360)