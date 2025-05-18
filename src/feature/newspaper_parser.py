import os
import uuid
import hashlib
import requests
import feedparser
from urllib.parse import urlparse
from newspaper import Article, build
from typing import List, Dict

news_sites = [
    "https://news.sky.com",
    "https://www.nytimes.com",
    "https://www.euronews.com/just-in",
    "https://www.theguardian.com/us-news",
    "https://newizv.ru/news",
    "https://www.bbc.com/news",
]

rss_map = {
    "https://news.sky.com": "https://feeds.skynews.com/feeds/rss/home.xml",
    "https://www.nytimes.com": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.euronews.com/just-in": "https://www.euronews.com/rss?level=theme&name=just_in",
    "https://www.theguardian.com/us-news": "https://www.theguardian.com/us-news/rss",
    "https://newizv.ru/news": "https://newizv.ru/rss",
    "https://www.bbc.com/news": "https://feeds.bbci.co.uk/news/rss.xml"
}
class NewsParser:
    def __init__(self, sites: List[str] = news_sites, media_dir: str = "./media"):
        self.sites = sites
        self.media_dir = media_dir

        # Структура папок для медиа
        self.img_folder = os.path.join(self.media_dir, 'img')
        os.makedirs(self.img_folder, exist_ok=True)

    def generate_numeric_id(self, url: str, length: int = 6) -> int:
        md5_hash = hashlib.md5(url.encode()).hexdigest()
        numeric_part = ''.join(filter(str.isdigit, md5_hash))
        return int(numeric_part[:length] or '0')

    def get_latest_rss_url(self, rss_url: str) -> str:
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                return feed.entries[0].link
            else:
                print(f"RSS пустой: {rss_url}")
                return ""
        except Exception as e:
            print(f"Ошибка при парсинге RSS {rss_url}: {e}")
            return ""

    def get_latest_article_url(self, site_url: str) -> str:
        rss_url = rss_map.get(site_url)
        if rss_url:
            print(f"Используем RSS для {site_url}")
            article_url = self.get_latest_rss_url(rss_url)
            if article_url:
                return article_url

        print(f"Fallback на newspaper3k для {site_url}")
        try:
            source = build(site_url, memoize_articles=False)
            if source.articles:
                return source.articles[0].url
            else:
                print(f"Нет статей на сайте: {site_url}")
                return ""
        except Exception as e:
            print(f"Ошибка при обработке сайта {site_url}: {e}")
            return ""

    def save_media(self, url: str, media_type: str) -> str:
        try:
            random_id = uuid.uuid4().hex
            if media_type == 'img':
                file_extension = os.path.splitext(urlparse(url).path)[1] or '.jpg'
                filename = f"img-{random_id}{file_extension}"
                folder = self.img_folder
            else:
                print(f"Unknown media type: {media_type}")
                return None

            file_path = os.path.join(folder, filename)

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)

            return filename  # ← только имя файла
        except Exception as e:
            print(f"Ошибка при скачивании {url}: {e}")
            return None

    def parse_article(self, url: str, download_media: bool = True) -> Dict[str, str]:
        try:
            article = Article(url)
            article.download()
            article.parse()

            top_image_url = article.top_image if article.top_image else None
            top_image_local = []

            if download_media and top_image_url:
                local_filename = self.save_media(top_image_url, 'img')
                if local_filename:
                    top_image_local.append(local_filename)

            parsed_url = urlparse(url)
            source = parsed_url.netloc
            post_id = parsed_url.path.strip("/").split("/")[-1]

            return {
                "title": article.title,
                "text": article.text,
                "publish_date": str(article.publish_date) if article.publish_date else "Не указана",
                "url": url,
                "top_image_url": top_image_url,
                "top_image_local": top_image_local,
                "source": source,
                "post_id": post_id,
                "id": self.generate_numeric_id(url),
            }
        except Exception as e:
            print(f"Ошибка при парсинге статьи {url}: {e}")
            return {}

    def get_latest_articles(self) -> List[Dict[str, str]]:
        latest_articles = []
        for site in self.sites:
            print(f"\nОбработка сайта: {site}")
            latest_url = self.get_latest_article_url(site)
            if latest_url:
                article_data = self.parse_article(latest_url)
                if article_data:
                    latest_articles.append(article_data)
        return latest_articles
