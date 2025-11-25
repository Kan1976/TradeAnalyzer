import os
import sys

# Путь к папке с проектом
PROJECT_DIR = "/storage/emulated/0/TradeAnalyzer"

# Переходим в папку проекта
os.chdir(PROJECT_DIR)

# Добавляем её в системный путь, чтобы все модули находились
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

# Запуск основного файла
import main