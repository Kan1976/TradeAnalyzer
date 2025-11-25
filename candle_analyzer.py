from PIL import Image
import numpy as np
import os

# Параметры — при необходимости подправь (ширина области справа, число свечей)
RIGHT_REGION_RATIO = 0.6   # правая часть экрана: берем правую 60% (если свечи занимают ~2/3 экрана справа)
NUM_CANDLES = 20
SAMPLE_X_MARGIN = 10       # отступ слева внутри правой-области (px)
MIN_BODY_HEIGHT = 3        # минимальный размер тела свечи в px, чтобы считать не шумом

def crop_right_region(img):
    w, h = img.size
    left = int(w * (1 - RIGHT_REGION_RATIO))
    return img.crop((left, 0, w, h)), left

def estimate_candle_columns(region_img):
    """Разделяем правую область на NUM_CANDLES вертикальных колонок (по X).
       Возвращаем список x центров колонок (целые пиксели)."""
    w, h = region_img.size
    # оставляем небольшой отступ по краям
    usable_w = w - SAMPLE_X_MARGIN * 2
    step = usable_w / NUM_CANDLES
    centers = [int(SAMPLE_X_MARGIN + step * (i + 0.5)) for i in range(NUM_CANDLES)]
    return centers

def analyze_column(region_img, x):
    """По вертикальной колонке приближенно оцениваем open/high/low/close:
       - Находим сверху/снизу значимые изменения по яркости цвета тела (зел/крас).
       - Вернём (open_px, close_px, high_px, low_px, color)
       px — координаты по Y (0 сверху). color: 'up' или 'down' или 'neutral'."""
    px = region_img.load()
    w, h = region_img.size

    # собираем средние цвета по горизонтальной полосе +-1 пикселя по X
    col_vals = []
    for y in range(h):
        cnt = 0
        r_sum = g_sum = b_sum = 0
        for dx in (-1, 0, 1):
            xx = min(max(x + dx, 0), w - 1)
            r,g,b = px[xx, y][:3]
            r_sum += r; g_sum += g; b_sum += b
            cnt += 1
        col_vals.append((r_sum//cnt, g_sum//cnt, b_sum//cnt))
    # переведём в яркость/зеленость/красноту
    brightness = np.array([0.299*r + 0.587*g + 0.114*b for (r,g,b) in col_vals])
    green_ratio = np.array([g / (r+g+b+1e-6) for (r,g,b) in col_vals])
    red_ratio = np.array([r / (r+g+b+1e-6) for (r,g,b) in col_vals])

    # Ищем тело свечи: участок с высокой насыщенностью красного или зелёного
    # Находим места с локальной разницей цвета относительно соседей
    diff_green = np.abs(green_ratio - np.roll(green_ratio, 1))
    diff_red = np.abs(red_ratio - np.roll(red_ratio, 1))
    score = diff_green + diff_red
    # сглажим
    score_s = np.convolve(score, np.ones(5)/5, mode='same')

    # возьмём позиции самых больших score — кандидаты на границы тела
    threshold = np.percentile(score_s, 85)
    candidates = np.where(score_s >= threshold)[0]
    if candidates.size == 0:
        # не нашли явных тел — считаем нейтральной маленькой свечой
        middle = h // 2
        return {'open': middle+2, 'close': middle-2, 'high': middle+5, 'low': middle-5, 'color': 'neutral'}

    y_min = int(candidates.min())
    y_max = int(candidates.max())
    body_height = y_max - y_min
    if body_height < MIN_BODY_HEIGHT:
        # маленькое тело — нейтрально
        middle = (y_min + y_max)//2
        return {'open': middle+1, 'close': middle-1, 'high': y_min-3, 'low': y_max+3, 'color': 'neutral'}

    # определим цвет по средним ratios внутри тела
    mean_green = green_ratio[y_min:y_max+1].mean()
    mean_red = red_ratio[y_min:y_max+1].mean()
    color = 'up' if mean_green > mean_red else 'down'

    # Высота фитилей: ищем ближайшую яркую точку сверху/снизу (по brightness)
    # high — минимальный y с brightness резко отличающейся от фонового
    bright_diff = np.abs(brightness - np.median(brightness))
    high_candidates = np.where((bright_diff[:y_min] > np.percentile(bright_diff, 70)))[0]
    if high_candidates.size:
        high = high_candidates.min()
    else:
        high = max(y_min-5,0)
    low_candidates = np.where((bright_diff[y_max+1:] > np.percentile(bright_diff, 70)))[0]
    if low_candidates.size:
        low = (y_max+1) + low_candidates.max()
    else:
        low = min(y_max+5, h-1)

    # open/close: ориентируемся на относительное положение: для зелёной (up) open > close по Y (y увеличивается вниз)
    # возьмём верхнюю/нижнюю границы тела
    open_px = y_max if color == 'up' else y_min
    close_px = y_min if color == 'up' else y_max

    return {'open': int(open_px), 'close': int(close_px), 'high': int(high), 'low': int(low), 'color': color}

def extract_candles_from_image(image_path):
    """Возвращает список свечей [левые→правые], каждая — dict с open/close/high/low (px) и color."""
    img = Image.open(image_path).convert('RGB')
    region, left_offset = crop_right_region(img)
    centers = estimate_candle_columns(region)
    candles = []
    for x in centers:
        c = analyze_column(region, x)
        candles.append(c)
    # порядок: левые→правые (как на экране слева->справа)
    return candles

def features_from_candles(candles):
    """Делаем простые числовые признаки: к-во up/down, last change, range ratios, slope"""
    closes = []
    colors = []
    for c in candles:
        # используем 'price' как вертикальную координату close (чем меньше px — выше цена)
        closes.append(c['close'])
        colors.append(c['color'])
    closes = np.array(closes, dtype=float)
    # Инвертируем px в относительную цену: smaller px -> larger price; нормируем
    inv = (closes.max() - closes)  # higher means higher price
    # признаки
    diffs = np.diff(inv)
    last_change = diffs[-1] if diffs.size else 0.0
    avg_change = diffs.mean() if diffs.size else 0.0
    up_count = sum(1 for col in colors if col == 'up')
    down_count = sum(1 for col in colors if col == 'down')
    volatility = np.std(diffs) if diffs.size else 0.0
    range_ratio = (inv.max() - inv.min()) / (np.mean(inv) + 1e-6)
    # slope of last N (linear fit)
    x = np.arange(len(inv))
    if len(inv) >= 3:
        coef = np.polyfit(x, inv, 1)[0]
    else:
        coef = 0.0
    return {
        'last_change': float(last_change),
        'avg_change': float(avg_change),
        'up_count': int(up_count),
        'down_count': int(down_count),
        'volatility': float(volatility),
        'range_ratio': float(range_ratio),
        'slope': float(coef),
    }

def rule_predict(features):
    """Простое правило: комбинируем slope / last_change / counts -> вероятность"""
    score = 0.0
    score += features['slope'] * 2.0
    score += features['last_change'] * 1.5
    score += (features['up_count'] - features['down_count']) * 0.3
    # normalize roughly to probability 0..1 by sigmoid
    prob = 1.0 / (1.0 + np.exp(-score))
    direction = 'UP' if prob > 0.55 else ('DOWN' if prob < 0.45 else 'NEUTRAL')
    # scale confidence to percent
    confidence = round(float(abs(prob - 0.5) * 2.0 * 100.0), 2)  # 0..100, 0 means neutral
    if direction == 'NEUTRAL':
        confidence = 50.0
    return direction, confidence

def predict_from_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(image_path)
    candles = extract_candles_from_image(image_path)
    feats = features_from_candles(candles)
    direction, confidence = rule_predict(feats)
    # экспирация: если слабая уверенность -> 1 мин, средняя -> 2 мин, сильная -> 3 мин
    if confidence < 55:
        expiry = 1
    elif confidence < 75:
        expiry = 2
    else:
        expiry = 3
    return {
        'signal': direction,
        'confidence': confidence,
        'expiry_min': expiry,
        'features': feats,
        'candles_px': candles
    }

if __name__ == "__main__":
    # быстрый тест на последнем скриншоте в папке screenshots
    import glob
    files = sorted(glob.glob("screenshots/*.png"))
    if not files:
        print("Нет скриншотов в screenshots/")
    else:
        res = predict_from_image(files[-1])
        print(res)
