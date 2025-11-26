import time
import os
from analyzer import Analyzer

WATCH_DIR = "screenshots"

def watch_and_analyze():
    print("📡 Real-time analyzer запущен. Ожидание новых скриншотов...")

    analyzer = Analyzer()
    processed = set()

    while True:
        files = sorted(os.listdir(WATCH_DIR))

        for f in files:
            if f.endswith(".png") and f not in processed:
                full_path = os.path.join(WATCH_DIR, f)
                print(f"\n🔍 Найден новый скриншот: {f}")

                try:
                    signal, prob, exp = analyzer.analyze_image(full_path)

                    print(f"➡ Сигнал: {signal}")
                    print(f"📊 Вероятность: {prob}%")
                    print(f"⏱ Экспирация: {exp}")

                except Exception as e:
                    print(f"❌ Ошибка анализа: {e}")

                processed.add(f)

        time.sleep(3)

if __name__ == "__main__":
    watch_and_analyze()
