import os
from datetime import datetime

# Папка куда сохраняем скриншоты
SCREENSHOT_DIR = "screenshots"

# Создаём папку если её нет
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)


def save_screenshot(image_bytes):
    """
    Сохраняет изображение, переданное из приложения,
    например снимок экрана графика.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOT_DIR}/shot_{timestamp}.png"

    with open(filename, "wb") as f:
        f.write(image_bytes)

    print("Saved:", filename)
    return filename