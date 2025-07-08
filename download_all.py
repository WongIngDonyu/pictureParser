from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from bd import init_db
from download_picture import download_wallpaper
from utils import get_random_headers
import time

def download_all_from_main_page():
    base_url = "https://wallscloud.net"
    page = 1
    while True:
        page_url = f"{base_url}/ru?page={page}"
        print(f"\nОбрабатывается страница {page_url}")
        resp = requests.get(page_url, headers=get_random_headers())
        soup = BeautifulSoup(resp.text, "html.parser")
        wallpaper_links = soup.select("a.wall_link")
        if not wallpaper_links:
            print("Больше страниц нет. Завершено.")
            break
        print(f"Найдено ссылок: {len(wallpaper_links)}")
        for a_tag in wallpaper_links:
            href = a_tag.get("href")
            if href:
                wallpaper_url = urljoin(base_url, href)
                try:
                    download_wallpaper(wallpaper_url)
                except Exception as e:
                    print(f"Ошибка при обработке {wallpaper_url}: {e}")
        page += 1
        time.sleep(1)

if __name__ == "__main__":
    init_db()
    download_all_from_main_page()