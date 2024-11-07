import re
import time
from datetime import datetime

from src.Request.schemas import NewsExistsResponseModel, NewsExistsRequestModel, NewPostRequestModel, \
    NewPostResponseModel
from src.conf import api
from src.feature.TelegramParser import TelegramLastNews


def extract_channel_and_post_id(url):
    match = re.search(r'https://t\.me/s/([^/]+)/(\d+)', url)
    if match:
        channel_name = match.group(1)
        post_id = match.group(2)
        return channel_name, post_id
    return None, None


def get_news(channel=str, id_post=int) -> NewsExistsResponseModel:
    params = NewsExistsRequestModel(channel=channel, id_post=id_post)
    response = api.get("exists/{channel}/{id_post}", path_params=params, response_model=NewsExistsResponseModel)
    return response


def create_news(channel: str, id_post: int, time: datetime, url: str):
    data = NewPostRequestModel(channel=channel, id_post=id_post, time=time, url=url)
    api.post("create", data=data, response_model=NewPostResponseModel)
    return

def get_telegram_news():
    list_channels: list = ["netstalkers", "omanko"]
    parser = TelegramLastNews()
    for channel in list_channels:
        last_news = parser.get(channel)
        channel_name, post_id = extract_channel_and_post_id(last_news[0]["url"])
        if get_news(channel=channel_name, id_post=post_id).exists:
            create_news(channel=channel_name, id_post=post_id, time=last_news[0]["date"], url=last_news[0]["url"])


if __name__ == '__main__':
    while True:
        get_telegram_news()
        time.sleep(360)
