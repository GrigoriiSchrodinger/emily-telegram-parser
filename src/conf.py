from src.redis.RedisManager import RedisQueue
from src.request.RequestHandler import RequestHandler

api = RequestHandler(base_url="http://emily-database-handler:8000")
redis = RedisQueue(queue_name="filter", host="redis", port=6379, db=0)
