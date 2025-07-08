import os

import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

from bd import Picture, Category, session, init_db
from utils import generate_filename, safe_dir_name, get_random_headers


def download_wallpaper(page_url):
    headers = get_random_headers()
    resp = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    name_tag = soup.find("h1")
    name = name_tag.text.strip() if name_tag else "Unnamed"
    existing = session.query(Picture).filter_by(name=name).first()
    if existing:
        print(f"Пропущено: {name} уже существует в базе.")
        return
    parts = page_url.split("/")
    category_name = parts[6] if len(parts) > 6 else "Uncategorized"
    safe_category = safe_dir_name(category_name)
    dir_path = os.path.join("pictures", safe_category)
    os.makedirs(dir_path, exist_ok=True)
    category = session.query(Category).filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        session.add(category)
        session.commit()
    resolution_tag = soup.find(text=lambda t: t and "Разрешение:" in t)
    if resolution_tag:
        res_text = resolution_tag.split(":")[1].strip()
        width, height = [int(x.strip()) for x in res_text.split("x")]
    else:
        width, height = 0, 0
    tag_div = soup.find("div", class_="wallpaper-tags")
    tags = ", ".join([a.get_text(strip=True) for a in tag_div.find_all("a")]) if tag_div else ""
    download_url = page_url.rstrip("/") + "/original/download"
    image_resp = requests.get(download_url, headers=headers, allow_redirects=True)
    image_url = image_resp.url
    image = Image.open(BytesIO(image_resp.content))
    if width == 0 or height == 0:
        width, height = image.size
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
        fileName=full_path
    )
    session.add(picture)
    session.commit()
    print(f"Скачано и сохранено: {name} ({width}x{height}) — категория: {category.name}")