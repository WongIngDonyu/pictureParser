import time
from urllib.parse import urljoin
from threading import Lock, Thread

import requests
from bs4 import BeautifulSoup

from bd import init_db
from download_picture import download_wallpaper
from utils import get_random_headers

page_counter = 1
page_lock = Lock()

def get_next_page():
    global page_counter
    with page_lock:
        current = page_counter
        page_counter += 1
    return current

def process_pages_thread(base_url, thread_id):
    while True:
        page = get_next_page()
        page_url = f"{base_url}/ru?page={page}"
        print(f"[Поток {thread_id}] Обработка страницы {page_url}")
        try:
            resp = requests.get(page_url, headers=get_random_headers(), timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            wallpaper_links = soup.select("a.wall_link")
            if not wallpaper_links:
                print(f"[Поток {thread_id}] Ссылок нет. Завершаю.")
                break
            for a_tag in wallpaper_links:
                href = a_tag.get("href")
                if href:
                    wallpaper_url = urljoin(base_url, href)
                    try:
                        download_wallpaper(wallpaper_url)
                    except Exception as e:
                        print(f"[Поток {thread_id}] Ошибка при скачивании {wallpaper_url}: {e}")
            time.sleep(0.5)
        except Exception as e:
            print(f"[Поток {thread_id}] Ошибка при загрузке страницы {page_url}: {e}")
            break

def download_all_multithreaded(num_threads):
    base_url = "https://wallscloud.net"
    threads = []

    for i in range(num_threads):
        t = Thread(target=process_pages_thread, args=(base_url, i + 1))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("Загрузка завершена.")

if __name__ == "__main__":
    init_db()
    try:
        num_threads = int(input("Введите количество потоков: "))
        if num_threads < 1:
            raise ValueError
    except ValueError:
        print("Ошибка: введите корректное число больше 0.")
        exit(1)

    download_all_multithreaded(num_threads)