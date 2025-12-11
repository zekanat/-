import json
import os

DATA_FILE = 'data.json'

# начальное состояние
data = {
    'trainers': [],
    'rooms': [],
    'class_types': [],
    'scheduled_classes': [],
    'clients': [],
    'enrollments': []
}


def load_data():
    """Загрузка данных из JSON, если файл существует"""
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)


def save_data():
    """Сохранение данных в JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# загрузить данные при импорте модуля
load_data()
