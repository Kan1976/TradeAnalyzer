import cv2
import numpy as np

class Analyzer:

    def analyze(self, img):
        h, w = img.shape[:2]

        # --- Зона свечей (примерно 1/3 сверху экрана) ---
        candles_roi = img[int(h*0.15):int(h*0.55), int(w*0.1):int(w*0.9)]
        gray = cv2.cvtColor(candles_roi, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

        # --- Контуры свечей ---
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candle_centers = []

        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)

            # фильтрация мелких точек
            if ch < 20 or cw < 5:
                continue

            cx = x + cw // 2
            cy = y + ch // 2
            candle_centers.append((cx, cy))

        candle_centers = sorted(candle_centers)

        # --- Определение тренда ---
        trend = "FLAT"
        probability = 50.0

        if len(candle_centers) >= 3:
            y1 = candle_centers[0][1]
            y2 = candle_centers[-1][1]

            if y2 < y1 - 5:
                trend = "UP"
                probability = 65.0
            elif y2 > y1 + 5:
                trend = "DOWN"
                probability = 65.0

        # --- Уровни поддержки/сопротивления ---
        support = np.min([cy for _, cy in candle_centers]) if candle_centers else None
        resistance = np.max([cy for _, cy in candle_centers]) if candle_centers else None

        # --- Сигнал ---
        if trend == "UP":
            signal = "BUY"
        elif trend == "DOWN":
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        return {
            "signal": signal,
            "prob": probability,
            "trend": trend,
            "support_px": int(support) if support else 0,
            "resistance_px": int(resistance) if resistance else 0
        }