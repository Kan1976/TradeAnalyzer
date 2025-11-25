#!/usr/bin/env python3
# real_time_service.py
# Смотрит папку screenshots, анализирует новые скрины через candle_analyzer.predict_from_image
# Сохраняет last_signal.json и отправляет POST на overlay сервер /signal/start (если он запущен).

import os
import time
import json
import requests
from datetime import datetime

WATCH_FOLDER = "screenshots"
LAST_SIGNAL_FILE = "last_signal.json"
POLL_INTERVAL = 2.0  # сек
OVERLAY_SERVER = "http://127.0.0.1:5000"  # если overlay сервер запущен на телефоне
SEND_TO_OVERLAY = True  # выставь False, если не нужен POST

# Попробуем импортировать анализатор (candle_analyzer.py). Если нет — попробуем real_time_analyzer
try:
    from candle_analyzer import predict_from_image
except Exception:
    try:
        from real_time_analyzer import analyze_candles as _analyze
        def predict_from_image(path):
            # адаптер: real_time_analyzer возвращает dict с полями signal/probability
            from PIL import Image
            img = Image.open(path).convert("RGB")
            res = _analyze(img)  # если _analyze ожидает Image
            # если _analyze вернул None
            if res is None:
                raise RuntimeError("analyze returned None")
            # приведение к единому формату
            return {
                "signal": res.get("signal"),
                "confidence": res.get("probability") if res.get("probability") is not None else res.get("prob"),
                "expiry_min": res.get("expiry_min", 1),
                "meta": res
            }
    except Exception as e:
        print("Не удалось найти candle_analyzer или real_time_analyzer:", e)
        raise SystemExit(1)

def save_last_signal(data: dict):
    with open(LAST_SIGNAL_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_to_overlay(data: dict):
    if not SEND_TO_OVERLAY:
        return
    try:
        url = OVERLAY_SERVER.rstrip("/") + "/signal/start"
        r = requests.post(url, json=data, timeout=3)
        # не критично — просто логируем
        print("POST to overlay:", r.status_code, r.text[:200])
    except Exception as e:
        print("Ошибка отправки на overlay:", e)

def watch_loop():
    seen = set()
    if not os.path.exists(WATCH_FOLDER):
        print("Папка screenshots не найдена:", WATCH_FOLDER)
        return
    print("Real-time service started, watching", WATCH_FOLDER)
    while True:
        try:
            files = sorted(
                [f for f in os.listdir(WATCH_FOLDER) if f.lower().endswith(('.png','.jpg','.jpeg'))],
                key=lambda p: os.path.getmtime(os.path.join(WATCH_FOLDER, p))
            )
            for fn in files:
                full = os.path.join(WATCH_FOLDER, fn)
                if full in seen:
                    continue
                seen.add(full)
                print("🔍 Новый скрин:", fn)
                try:
                    res = predict_from_image(full)
                except Exception as e:
                    print("Ошибка анализа изображения:", e)
                    continue
                # Унифицированный формат
                signal = res.get("signal", "NEUTRAL")
                confidence = float(res.get("confidence", 50.0))
                out = {
                    "signal": signal,
                    "confidence": confidence,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_file": fn,
                    "details": res.get("meta", res)
                }
                save_last_signal(out)
                print("➡ Сигнал:", signal)
                print("📊 Вероятность:", confidence)
                # отправляем на overlay (если включено)
                try:
                    send_to_overlay(out)
                except Exception as e:
                    print("Ошибка отправки:", e)
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("Stopped by user")
            break
        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(3)

if __name__ == "__main__":
    watch_loop()
