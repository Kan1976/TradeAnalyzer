from flask import Flask, send_from_directory, jsonify, request
import os
import datetime

app = Flask(__name__, static_folder="overlay_app/static")

# -----------------------------
#   Главная HTML страница
# -----------------------------
@app.route("/")
def index():
    return send_from_directory("overlay_app", "overlay.html")

# -----------------------------
#   Статические файлы
# -----------------------------
@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("overlay_app/static", path)

# -----------------------------
#   Данные для оверлея
# -----------------------------
@app.route("/data")
def data():
    return jsonify({
        "status": "ok",
        "message": "Overlay работает!",
        "value": 123
    })

# -----------------------------
#   Запуск сигнала
# -----------------------------
@app.route("/signal/start", methods=["POST"])
def start_signal():
    # позже тут будет вызов анализа
    return jsonify({"status": "ok", "message": "signal started"})

# -----------------------------
#   Запись результата сделки
# -----------------------------
def save_feedback(result: str):
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("feedback.log", "a") as f:
        f.write(f"{t} - {result}\n")

@app.route("/feedback/success", methods=["POST"])
def feedback_success():
    save_feedback("SUCCESS")
    return jsonify({"status": "ok", "message": "успешная сделка сохранена"})

@app.route("/feedback/fail", methods=["POST"])
def feedback_fail():
    save_feedback("FAIL")
    return jsonify({"status": "ok", "message": "неуспешная сделка сохранена"})

# -----------------------------
#   Запуск сервера
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)