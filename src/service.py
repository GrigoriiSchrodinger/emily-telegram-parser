from src.redis.RedisManager import RedisQueue
from src.request.RequestHandler import RequestHandler
from src.service_url import get_url_redis, get_url_emily_database_handler

api = RequestHandler(base_url=get_url_emily_database_handler())
redis = RedisQueue(queue_name="filter", host=get_url_redis(), port=6379, db=0)
