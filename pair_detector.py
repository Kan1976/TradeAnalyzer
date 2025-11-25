import re
from PIL import Image
import pytesseract
import os

# Папка со скриншотами
SCREEN_PATH = "/storage/emulated/0/TradeAnalyzer/screenshots/"


def extract_pair_from_image(image_path):
    """
    Извлекает название валютной пары со скриншота.
    """
    try:
        img = Image.open(image_path)

        # OCR извлечение текста
        text = pytesseract.image_to_string(img, lang="eng")

        # Ищем пары вида XXX/YYY
        match = re.search(r"[A-Z]{3}/[A-Z]{3}", text)
        if match:
            return match.group(0)

        return "UNKNOWN"

    except Exception as e:
        return f"ERROR: {e}"


def detect_otc(image_path):
    """
    Определяет OTC ли это по тексту.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="eng")

        if "OTC" in text.upper():
            return True

        return False

    except Exception:
        return False


def analyze_latest_screenshot():
    """
    Анализ последнего скрина:
    - валютная пара
    - OTC или не OTC
    """

    files = sorted(os.listdir(SCREEN_PATH))
    if not files:
        return {"error": "no screenshots"}

    last_file = SCREEN_PATH + files[-1]

    pair = extract_pair_from_image(last_file)
    otc = detect_otc(last_file)

    return {
        "pair": pair,
        "otc": otc,
        "file": last_file
    }