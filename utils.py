import random
import re
import hashlib

from fake_useragent import UserAgent
from transliterate import translit

def generate_filename(name):
    name_translit = translit(name, 'ru', reversed=True)
    name_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', name_translit)
    name_clean = re.sub(r'_+', '_', name_clean).strip("_")
    short_hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:6]
    return f"{name_clean}_{short_hash}.jpg"

def safe_dir_name(name):
    name = translit(name, 'ru', reversed=True)
    return "".join(c for c in name if c.isalnum() or c in "_-").strip("_")

ua = UserAgent()

desktop_browsers = [
    ua.chrome,
    ua.firefox,
    ua.safari,
    ua.edge,
    ua.opera
]

def get_random_headers():
    try:
        user_agent = random.choice(desktop_browsers)
        return {"User-Agent": user_agent}
    except:
        return {"User-Agent": "Mozilla/5.0"}