import json
import logging

import requests

from src.service_url import get_url_loki


class LokiHandler(logging.Handler):
    def __init__(self, url, tags):
        super().__init__()
        self.url = url
        self.base_tags = tags

    def emit(self, record):
        try:
            tags = {
                **self.base_tags,
                **getattr(record, 'tags', {}),
                "level": record.levelname,
                "module": record.module,
                "function": record.funcName
            }

            # Преобразуем числовые значения
            numeric_fields = {}
            for key, value in tags.items():
                if isinstance(value, (int, float)):
                    numeric_fields[key] = value
                    tags[key] = str(value)

            log_entry = self.format(record)
            
            payload = {
                "streams": [
                    {
                        "stream": tags,
                        "values": [
                            [
                                str(int(record.created * 1e9)),
                                json.dumps({
                                    "message": log_entry,
                                    **numeric_fields
                                }, ensure_ascii=False)
                            ]
                        ]
                    }
                ]
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.url, data=json.dumps(payload), headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Loki logging error: {str(e)}")


logger = logging.getLogger("TelegramParser")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s"
))
logger.addHandler(console_handler)

loki_handler = LokiHandler(
    url=f"{get_url_loki()}/loki/api/v1/push",
    tags={"project": "TelegramParser"},
)
logger.addHandler(loki_handler)
