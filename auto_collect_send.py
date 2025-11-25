# auto_collect_send.py
import os
import time
import shutil
from machine_learning import predict_direction

try:
    import androidhelper
except ImportError:
    import sl4a as androidhelper  # для Pydroid

droid = androidhelper.Android()

SCREENSHOT_FOLDER = "screenshots"
BATCH_FOLDER = "batch_send"
BATCH_SIZE = 1000
SERVER_IP = "192.168.1.100"  # замените на IP вашего ноутбука
SERVER_FOLDER = "/home/user/TradeScreenshots"  # папка на ноутбуке

# Создаём папку для временного пакета
if not os.path.exists(BATCH_FOLDER):
    os.makedirs(BATCH_FOLDER)

def take_screenshot():
    ts = time.strftime("%Y%m%d-%H%M%S")
    filepath = os.path.join(SCREENSHOT_FOLDER, f"Screenshot_{ts}.png")
    droid.screenshot(filepath)
    return filepath

def choose_expiration(probability):
    if probability < 0.7:
        return 1
    elif probability < 0.85:
        return 3
    else:
        return 5

def send_batch_to_server(batch_folder=BATCH_FOLDER):
    """
    Отправка пакета скриншотов на ноутбук через scp.
    Нужно, чтобы на ноутбуке был доступ по SSH.
    """
    os.system(f"scp {batch_folder}/*.png user@{SERVER_IP}:{SERVER_FOLDER}")
    # После отправки очищаем папку
    for f in os.listdir(batch_folder):
        os.remove(os.path.join(batch_folder, f))
    print(f"✅ Пакет отправлен на сервер {SERVER_IP}")

def main():
    collected_count = 0
    print("Авто-сбор скриншотов с отправкой на ноутбук каждые 1000 штук")
    
    while True:
        screenshot_path = take_screenshot()
        signal, prob = predict_direction()
        exp = choose_expiration(prob/100)
        collected_count += 1

        # Копируем скриншот в папку пакета
        shutil.copy(screenshot_path, BATCH_FOLDER)

        print(f"[{time.strftime('%H:%M:%S')}] {screenshot_path} | Сигнал: {signal} | Вероятность: {prob:.2f}% | Экспирация: {exp} мин | Собрано: {collected_count}")

        if collected_count >= BATCH_SIZE:
            send_batch_to_server()
            collected_count = 0

        time.sleep(60 + int.from_bytes(os.urandom(1), 'big')/255*120)

if __name__ == "__main__":
    main()