import time

from src.feature.TelegramParser import TelegramLastNews


def get_telegram_news():
    list_channels: list = ["netstalkers", "omanko"]
    list_last_news: list = []
    parser = TelegramLastNews()
    for channel in list_channels:
        last_news = parser.get(channel)
        list_last_news.append(last_news)
    print(list_last_news)

if __name__ == '__main__':
    while True:
        get_telegram_news()
        time.sleep(10)