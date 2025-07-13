import os
import time
from http.client import IncompleteRead
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image

from bd import Picture, Category, Session
from cache import existing_urls
from utils import generate_filename, safe_dir_name, get_random_headers


def download_wallpaper(page_url):
    session = Session()

    try:
        headers = get_random_headers()
        resp = requests.get(page_url, headers=headers)
        if resp.status_code != 200:
            print(f"[!] Страница {page_url} вернула статус {resp.status_code}")
            return

        if "Language pack for code" in resp.text:
            print(f"[!] Пропущено: языковой пакет недоступен для {page_url}")
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        download_url = page_url.rstrip("/") + "/original/download"

        image = None
        image_url = None

        for attempt in range(3):
            try:
                image_resp = requests.get(download_url, headers=headers, allow_redirects=True, timeout=15)
                image_resp.raise_for_status()

                try:
                    image = Image.open(BytesIO(image_resp.content))
                    image.verify()
                    image = Image.open(BytesIO(image_resp.content))
                except Exception:
                    print(f"[!] Ответ не является изображением: {download_url}")
                    return

                image = Image.open(BytesIO(image_resp.content))
                image_url = image_resp.url
                break

            except IncompleteRead as e:
                print(f"[!] Попытка {attempt + 1}: IncompleteRead — {e}")
                if attempt == 2:
                    raise
                time.sleep(1)

            except Exception as e:
                print(f"[!] Ошибка загрузки изображения (попытка {attempt + 1}): {e}")
                if attempt == 2:
                    raise
                time.sleep(1)

        if image is None:
            print("[!] Не удалось загрузить изображение.")
            return

        if image_url in existing_urls:
            print(f"Пропущено: изображение по URL {image_url} уже существует в базе.")
            return

        name_tag = soup.find("h1")
        name = name_tag.text.strip() if name_tag else "Unnamed"

        parts = page_url.split("/")
        category_name = parts[5] if len(parts) > 5 else "Uncategorized"
        safe_category = safe_dir_name(category_name)
        dir_path = os.path.join("pictures", safe_category)
        os.makedirs(dir_path, exist_ok=True)

        category = session.query(Category).filter_by(name=category_name).first()
        if not category:
            try:
                category = Category(name=category_name)
                session.add(category)
                session.commit()
            except Exception:
                session.rollback()
                category = session.query(Category).filter_by(name=category_name).first()

        resolution_tag = soup.find(text=lambda t: t and "Разрешение:" in t)
        if resolution_tag:
            res_text = resolution_tag.split(":")[1].strip()
            try:
                width, height = [int(x.strip()) for x in res_text.split("x")]
            except Exception:
                width, height = image.size
        else:
            width, height = image.size

        tag_div = soup.find("div", class_="wallpaper-tags")
        tags = ", ".join([a.get_text(strip=True) for a in tag_div.find_all("a")]) if tag_div else ""

        filename = generate_filename(name)
        full_path = os.path.join(dir_path, filename)
        with open(full_path, "wb") as f:
            f.write(image_resp.content)

        picture = Picture(
            name=name,
            category_id=category.id,
            tags=tags,
            width=width,
            height=height,
            url=image_url,
            fileName=filename
        )
        session.add(picture)
        session.commit()
        existing_urls.add(image_url)

        print(f"Скачано и сохранено: {name} ({width}x{height}) — категория: {category.name}")

    except Exception as e:
        session.rollback()
        print(f"[!] Ошибка при обработке {page_url}: {e}")

    finally:
        session.close()
