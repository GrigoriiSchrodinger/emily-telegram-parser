from src.redis.RedisManager import RedisQueue
from src.request.RequestHandler import RequestHandler

api = RequestHandler(base_url="http://0.0.0.0:8000/news")
redis = RedisQueue(queue_name="processing", host="localhost", port=6379, db=0)
