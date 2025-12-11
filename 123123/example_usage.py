import requests
from datetime import datetime

BASE_URL = 'http://localhost:5000'


def main():
    # 1. Тренер
    trainer = {
        'name': 'Иван Петров',
        'specialization': 'Йога',
        'max_classes_per_day': 6
    }
    print('Создаём тренера...')
    print(requests.post(f'{BASE_URL}/trainers', json=trainer).json())

    # 2. Зал
    room = {
        'name': 'Студия А',
        'capacity': 20
    }
    print('Создаём зал...')
    print(requests.post(f'{BASE_URL}/rooms', json=room).json())

    # 3. Тип занятия
    class_type = {
        'name': 'Йога для начинающих',
        'duration_minutes': 60
    }
    print('Создаём тип занятия...')
    print(requests.post(f'{BASE_URL}/class-types', json=class_type).json())

    # 4. Клиент
    client = {
        'name': 'Мария Сидорова',
        'email': 'maria@example.com'
    }
    print('Создаём клиента...')
    print(requests.post(f'{BASE_URL}/clients', json=client).json())

    # 5. Занятие
    now = datetime.now()
    scheduled_class = {
        'class_type_id': 1,
        'trainer_id': 1,
        'room_id': 1,
        'start_time': now.replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
        'end_time': now.replace(hour=11, minute=0, second=0, microsecond=0).isoformat(),
        'max_enrollment': 20
    }
    print('Создаём занятие...')
    print(requests.post(f'{BASE_URL}/schedule', json=scheduled_class).json())

    # 6. Запись на занятие
    enrollment = {
        'scheduled_class_id': 1,
        'client_id': 1
    }
    print('Записываем клиента...')
    print(requests.post(f'{BASE_URL}/enroll', json=enrollment).json())

    # 7. Статистика
    print('Статистика:')
    print(requests.get(f'{BASE_URL}/analytics').json())


if __name__ == '__main__':
    main()
