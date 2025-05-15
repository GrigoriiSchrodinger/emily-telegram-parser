import asyncio
import os
import json
import re
import time
from typing import Any
from src.feature.TeleParser import TeleScraperDict
from src.feature.TelegramParser import TelegramLastNews
from src.request.schemas import NewsExistsResponseModel, NewsExistsRequestModel, NewPostResponseModel, \
    NewPostRequestModel, UploadMediaPathParams
from src.logger import logger
from src.service import redis, api


def filter_outlinks_in_news_list(news_list: list[dict]) -> list[dict]:
    """
    Фильтрует t.me-ссылки в outlinks для всего списка новостей.
    Возвращает новый список новостей с очищенными ссылками.
    Сохраняет исходные данные неизменными.
    """
    filtered_news = []
    for news in news_list:
        if 'outlinks' in news and isinstance(news['outlinks'], list):
            # Фильтруем ссылки, удаляя содержащие https://t.me/
            filtered_links = [link for link in news['outlinks'] if 'https://t.me/' not in link]
            # Создаем копию новости с обновленными ссылками
            filtered_news.append({**news, 'outlinks': filtered_links})
        else:
            # Если нет outlinks - оставляем как есть
            filtered_news.append(news)
    return filtered_news

def extract_channel_and_post_id(url: str) -> tuple[str | Any, ...] | tuple[None, None]:
    match = re.search(r'https://t\.me/s/([^/]+)/(\d+)', url)
    if not match:
        logger.warning("Не удалось распарсить URL", extra={"tags": {"url": url, "operation": "url_parsing"}})
    return match.groups() if match else (None, None)


def get_news(channel: str, id_post: int) -> NewsExistsResponseModel:
    logger.debug("Запрос к API на проверку новости", extra={"tags": {
        "channel": channel,
        "post_id": id_post,
        "api_operation": "check_news"
    }})
    params = NewsExistsRequestModel(channel=channel, id_post=id_post)
    response = api.get("all-news/exists-news/{channel}/{id_post}", path_params=params, response_model=NewsExistsResponseModel)
    logger.debug("Ответ API получен", extra={"tags": {
        "channel": channel,
        "post_id": id_post,
        "api_response": response.dict()
    }})
    return response


def create_news(channel: str, id_post: int, text: str, timestamp: str, url: str, outlinks: list) -> None:
    try:
        data = NewPostRequestModel(channel=channel, id_post=id_post, text=text, time=timestamp, url=url, outlinks=outlinks)
        logger.info("Отправка данных для создания новости", extra={"tags": {
            "channel": channel,
            "post_id": id_post,
            "data_length": len(text)
        }})
        api.post("all-news/create", data=data, response_model=NewPostResponseModel)
        logger.info("Новость успешно создана", extra={"tags": {
            "channel": channel,
            "post_id": id_post,
        }})
    except Exception as e:
        logger.error("Ошибка создания новости", extra={"tags": {
            "channel": channel,
            "post_id": id_post,
            "error": str(e)
        }})


async def upload_media_files(id_post: int, channel: str, images: list[str], videos: list[str]) -> dict:
    logger.info("Начало загрузки медиа", extra={"tags": {
        "channel": channel,
        "post_id": id_post,
        "total_files": len(images) + len(videos)
    }})
    files = []

    try:
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
            endpoint="media/upload/{id_post}/{channel}",
            path_params=path_params,
            files=files
        )
        if response:
            logger.info("Медиа загружено успешно", extra={"tags": {
                "channel": channel,
                "post_id": id_post,
                "uploaded_files": len(files),
                "response_status": response.get("status")
            }})
        else:
            logger.error("Ошибка загрузки медиа", extra={"tags": {
                "channel": channel,
                "post_id": id_post
            }})
        return response
    except Exception as e:
        logger.error("Ошибка при загрузке медиа", extra={"tags": {
            "channel": channel,
            "post_id": id_post,
            "error": str(e)
        }})
        return {}
    finally:
        logger.debug("Завершение обработки медиа-файлов", extra={"tags": {
            "channel": channel,
            "post_id": id_post,
            "closed_files": len(files)
        }})
        for file_tuple in files:
            try:
                file_tuple[1][1].close()
            except:
                pass

def get_telegram_news():
    try:
        logger.info("Запуск цикла сбора новостей")
        channels = ["exploitex", "moscowmap", "whackdoor", "moscowachplus", "novosti_efir", "moscow", "chp_sochi"]
        parser = TelegramLastNews()
        
        logger.info("Начало сбора новостей", extra={"tags": {"process": "news_collection"}})
        
        for channel in channels:
            logger.info(f"Обработка канала: {channel}", extra={"tags": {"channel": channel}})
            
            try:
                last_news = filter_outlinks_in_news_list(parser.get(channel))
                logger.debug(f"Получено {len(last_news)} новостей", extra={"tags": {"channel": channel}})
                logger.debug(f"Список новостей", extra={"tags": {"list_news": last_news}})

                for news in last_news:
                    channel_name, post_id = extract_channel_and_post_id(news["url"])
                    logger.debug(f"Обработка новости: {news['url']}", extra={"tags": {
                        "channel": channel_name,
                        "post_id": post_id
                    }})
                    
                    if channel_name and post_id:
                        exists_response = get_news(channel=channel_name, id_post=int(post_id))
                        logger.info(f"Проверка существования новости: {exists_response.exists}", extra={"tags": {
                            "channel": channel_name,
                            "post_id": post_id
                        }})
                        
                        if not exists_response.exists and news.get("content"):
                            # Логируем создание новой записи
                            logger.info("Создание новой записи", extra={"tags": {
                                "channel": channel_name,
                                "post_id": post_id,
                                "operation": "create_news"
                            }})
                            
                            create_news(channel=channel_name, id_post=int(post_id), timestamp=news.get("date"), 
                                      url=news["url"], text=news.get("content"), outlinks=news.get("outlinks"))

                            logger.debug("Получение медиа-контента", extra={"tags": {
                                "channel": channel_name,
                                "post_id": post_id,
                                "operation": "get_media"
                            }})
                            
                            scraper = TeleScraperDict(news["url"])
                            result = asyncio.run(scraper.get())
                            
                            if result.get('images') or result.get('videos'):
                                logger.info(f"Найдено медиа: {len(result.get('images', []))} изображений, "
                                          f"{len(result.get('videos', []))} видео", extra={"tags": {
                                              "channel": channel_name,
                                              "post_id": post_id,
                                              "media_operation": "upload"
                                          }})
                                
                                upload_result = asyncio.run(upload_media_files(
                                    images=result.get('images', []),
                                    videos=result.get('videos', []),
                                    id_post=post_id,
                                    channel=channel,
                                ))
                                logger.debug("Медиа успешно загружено", extra={"tags": {
                                    "channel": channel_name,
                                    "post_id": post_id,
                                    "media_operation": "success"
                                }})
                                
                            json_news = {"channel": channel_name, "content": news["content"], 
                                       "id_post": post_id, "outlinks": news["outlinks"]}
                            redis.send_to_queue(json.dumps(json_news))
                            logger.info("Новость добавлена в очередь Redis", extra={"tags": {
                                "channel": channel_name,
                                "post_id": post_id,
                                "operation": "redis_queue"
                            }})
                    else:
                        logger.warning("Не удалось извлечь channel_name или post_id", extra={"tags": {
                            "url": news["url"],
                            "channel": channel
                        }})
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке канала {channel}: {str(e)}", extra={"tags": {
                    "channel": channel,
                    "error_type": type(e).__name__
                }}, exc_info=True)
                continue
        logger.info("Цикл сбора новостей завершен", extra={"tags": {
            "processed_channels": len(channels)
        }})
    except Exception as e:
        logger.critical("Критическая ошибка в основном цикле", exc_info=True, extra={"tags": {
            "error_type": type(e).__name__
        }})


if __name__ == '__main__':
    while True:
        get_telegram_news()
        time.sleep(600)
