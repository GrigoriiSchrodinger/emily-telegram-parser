import json
import subprocess
from typing import List, Dict


class TelegramParser:
    def __init__(
            self,
            library="snscrape",
            max_results="1",
            type_channel="telegram-channel",
            json_parser="--jsonl-for-buggy-int-parser"
    ):
        self.library = library
        self.max_results = max_results
        self.type_channel = type_channel
        self.json_parser = json_parser

    @staticmethod
    def upgrade_to_json(data: str) -> List[Dict]:
        """
        Преобразует строку в формате JSON в Python-объект.
        """
        json_lines = data.strip().split('\n')
        posts: List[Dict] = [json.loads(line) for line in json_lines if line]
        return posts

    def subprocess_run(self, channel_url: str) -> str:
        """
        Выполняет команду для получения данных о последнем контенте с канала.
        """
        try:
            result = subprocess.run(
                [
                    self.library,
                    "--max-results",
                    self.max_results,
                    self.json_parser,
                    self.type_channel,
                    channel_url
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as error:
            print(f"Ошибка при запуске команды: {error}")
            return ""

class TelegramLastNews(TelegramParser):
    def get(self, telegram_channel: str) -> List[Dict]:
        """
        Получает последние новости с канала и возвращает их как Python-объекты.
        """
        data_last_news = self.subprocess_run(channel_url=telegram_channel)
        return self.upgrade_to_json(data_last_news)
