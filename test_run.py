# test_run.py
import os
from machine_learning import predict_direction

def main():
    screenshots_folder = "screenshots"

    # Получаем список файлов PNG в папке screenshots
    files = [f for f in os.listdir(screenshots_folder) if f.endswith(".png")]
    if not files:
        print("Нет скриншотов в папке screenshots/")
        return

    # Берём последний по времени изменения
    files.sort(key=lambda f: os.path.getmtime(os.path.join(screenshots_folder, f)), reverse=True)
    latest_file = files[0]
    filepath = os.path.join(screenshots_folder, latest_file)
    
    print(f"Используем скриншот: {filepath}")

    # Анализируем через модель
    signal = predict_direction()
    print(f"Сигнал: {signal}")

if __name__ == "__main__":
    main()