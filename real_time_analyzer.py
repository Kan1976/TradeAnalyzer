# real_time_analyzer.py
# Простой реальный-времени эвристический анализатор M1-скринов
# Помести файл в папку TradeAnalyzer и запусти: python3 real_time_analyzer.py

import os
import time
from PIL import Image
from statistics import median
from datetime import datetime

# ----- Настройки (подстрой под свой экран) -----
SCREENSHOTS_DIR = "screenshots"   # относительный путь в папке проекта
CROP = (40, 120, 680, 1000)       # (left, top, right, bottom) — ОБЯЗАТЕЛЬНО настроить под твой экран
CANDLES_TO_ANALYSE = 20          # сколько последних свечей анализируем
SAMPLE_COLS = 40                 # сколько колонок пробуем распределить по области (чем больше — тем точнее)
NEAR_LEVEL_PX = 12               # px — порог близости к уровню для повышения вероятности
POLL_INTERVAL = 2.0              # сек — как часто смотреть папку
RESULTS_CSV = "results.csv"

# ----- Вспомогательные -----
def is_red(rgb):
    r,g,b = rgb
    return (r > 100) and (r > g + 20) and (r > b + 20)

def is_green(rgb):
    r,g,b = rgb
    return (g > 100) and (g > r + 20) and (g > b + 20)

def analyze_candles(img):
    """
    Сканируем прямоугольник CROP, разбиваем по вертикали на SAMPLE_COLS сэмплов,
    для каждого сэмпла определяем цвет свечи и её high/low (по окрашенным пикселям).
    """
    left, top, right, bottom = CROP
    crop = img.crop((left, top, right, bottom))
    w, h = crop.size

    cols = []
    # равномерно распределим позиции по ширине (последние SAMPLE_COLS)
    for i in range(SAMPLE_COLS):
        x = int(w * (i + 0.5) / SAMPLE_COLS)
        cols.append(x)

    candle_infos = []
    for x in cols:
        # пробуем найти диапазон цветных пикселей по вертикали в этой колонке
        colored_pixels = []
        for y in range(h):
            px = crop.getpixel((x, y))
            # px может быть RGB или RGBA
            if len(px) == 4:
                px = px[:3]
            if is_red(px) or is_green(px):
                colored_pixels.append((y, px))
        if not colored_pixels:
            candle_infos.append(None)
            continue
        ys = [y for y, _ in colored_pixels]
        top_y = min(ys)
        bottom_y = max(ys)
        # определим средний цвет по центру сегмента
        mid_y = (top_y + bottom_y) // 2
        # возьмём несколько пикселей вокруг mid_y, если есть
        sample_colors = []
        for dy in range(-2, 3):
            yy = mid_y + dy
            if 0 <= yy < h:
                px = crop.getpixel((x, yy))
                if len(px) == 4:
                    px = px[:3]
                sample_colors.append(px)
        # средний цвет
        avg = tuple(sum(c[i] for c in sample_colors)//len(sample_colors) for i in range(3))
        color = 'green' if is_green(avg) else ('red' if is_red(avg) else 'none')
        candle_infos.append({
            'x': x,
            'top': top_y,
            'bottom': bottom_y,
            'color': color,
            'mid': (top_y + bottom_y) / 2
        })

    # очистим None и возьмём последние CANDLES_TO_ANALYSE валидных
    valid = [c for c in candle_infos if c is not None]
    if len(valid) < 3:
        return None  # мало данных
    # возьмём последние N
    valid = valid[-CANDLES_TO_ANALYSE:]
    highs = [v['top'] for v in valid]   # в пикселях top - меньшая y => выше цена (выровняем логикой)
    lows  = [v['bottom'] for v in valid]
    colors = [v['color'] for v in valid]

    # уровни: используем медиану low/high
    support_px = median(lows)
    resistance_px = median(highs)

    # last candle
    last = valid[-1]
    last_mid = last['mid']
    last_color = last['color']

    # расстояния до уровней
    dist_to_support = abs(last_mid - support_px)
    dist_to_resistance = abs(last_mid - resistance_px)

    # решение — эвристика:
    signal = None
    prob = 0.5

    # если близко к поддержке и свеча зелёная или есть отскок (последние 2 зелен)
    last_colors = colors[-3:]
    green_count = last_colors.count('green')
    red_count = last_colors.count('red')

    if dist_to_support <= NEAR_LEVEL_PX and green_count >= 1:
        signal = 'UP'
        prob = 0.6 + (NEAR_LEVEL_PX - dist_to_support)/ (NEAR_LEVEL_PX*2)
    elif dist_to_resistance <= NEAR_LEVEL_PX and red_count >= 1:
        signal = 'DOWN'
        prob = 0.6 + (NEAR_LEVEL_PX - dist_to_resistance)/ (NEAR_LEVEL_PX*2)
    else:
        # если доминируют зелёные — вверх, иначе вниз
        if green_count > red_count:
            signal = 'UP'
            prob = 0.55 + (green_count - red_count)*0.08
        elif red_count > green_count:
            signal = 'DOWN'
            prob = 0.55 + (red_count - green_count)*0.08
        else:
            signal = 'NEUTRAL'
            prob = 0.5

    # нормируем prob
    prob = max(0.5, min(prob, 0.99))
    # переведём пиксельные уровни обратно в "ценовое" относительное — мы возвращаем px, потому что без привязки к цене точную цену не получить.
    return {
        'signal': signal,
        'probability': round(prob * 100, 2),
        'support_px': support_px,
        'resistance_px': resistance_px,
        'dist_support_px': dist_to_support,
        'dist_resistance_px': dist_to_resistance,
        'last_color': last_color
    }

def log_result(filename, res):
    line = "{time},{file},{signal},{prob},{support_px},{resistance_px}\n".format(
        time=datetime.now().isoformat(),
        file=filename,
        signal=res.get('signal'),
        prob=res.get('probability'),
        support_px=int(res.get('support_px',0)),
        resistance_px=int(res.get('resistance_px',0))
    )
    # если файла нет — добавим заголовок
    newfile = not os.path.exists(RESULTS_CSV)
    with open(RESULTS_CSV, "a") as f:
        if newfile:
            f.write("time,file,signal,probability,support_px,resistance_px\n")
        f.write(line)

# ----- Основной цикл -----
def watch_and_analyze():
    seen = set()
    # убедимся что папка существует
    if not os.path.exists(SCREENSHOTS_DIR):
        print("Папка screenshots не найдена:", SCREENSHOTS_DIR)
        return

    print("Real-time analyzer started, watching", SCREENSHOTS_DIR)
    while True:
        try:
            files = sorted(
                [f for f in os.listdir(SCREENSHOTS_DIR) if f.lower().endswith(('.png','.jpg','.jpeg'))],
                key=lambda p: os.path.getmtime(os.path.join(SCREENSHOTS_DIR, p))
            )
            for fn in files:
                full = os.path.join(SCREENSHOTS_DIR, fn)
                if full in seen:
                    continue
                # новый файл
                seen.add(full)
                print("🔍 Новый скрин:", fn)
                try:
                    img = Image.open(full).convert("RGB")
                    print("Файл", fn, "открыт, размер", img.size)
                    res = analyze_candles(img)
                    if res is None:
                        print("❌ Не удалось извлечь свечи — проверь CROP и настройки")
                        continue
                    # печать результата
                    print("➡ Сигнал:", res['signal'])
                    print("📊 Вероятность:", f"{res['probability']}%")
                    print("support_px:", int(res['support_px']), "res_px:", int(res['resistance_px']))
                    # логируем
                    log_result(fn, res)
                except Exception as e:
                    print("Ошибка анализа:", e)
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("Stopped by user")
            break
        except Exception as e:
            print("Ошибка в основном цикле:", e)
            time.sleep(3)

if __name__ == "__main__":
    watch_and_analyze()