import pytesseract
from PIL import Image

# Путь к tesseract в Termux
TESSERACT_CMD = "/data/data/com.termux/files/usr/bin/tesseract"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def recognize_pair(image_path):
    """
    Распознаёт валютную пару и тип рынка (OTC/обычный).
    image_path — путь к скриншоту с названием валюты.
    """
    try:
        img = Image.open(image_path)

        # Распознаём текст
        text = pytesseract.image_to_string(img, lang="eng+rus")
        text = text.upper().replace(" ", "").strip()

        # Список популярных валютных пар
        pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
            "USDCAD", "USDCHF", "EURJPY", "GBPJPY",
            "NZDUSD", "EURGBP"
        ]

        recognized_pair = "UNKNOWN"
        for pair in pairs:
            if pair in text:
                recognized_pair = pair
                break

        # Определяем OTC
        is_otc = "OTC" in text

        return {
            "pair": recognized_pair,
            "otc": is_otc,
            "raw_text": text
        }

    except Exception as e:
        return {"error": str(e)}