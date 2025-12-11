from datetime import datetime, timedelta


def parse_dt(value: str) -> datetime:
    """Утилита: безопасный парсинг datetime из ISO-строки"""
    return datetime.fromisoformat(value)


def intervals_overlap(start1, end1, start2, end2) -> bool:
    """Проверка пересечения двух интервалов времени"""
    return not (end1 <= start2 or start1 >= end2)


def check_conflicts(new_class: dict, existing_classes: list) -> str | None:
    """
    Проверить конфликты при добавлении нового занятия.
    Возвращает текст ошибки или None.
    """
    start_time = parse_dt(new_class['start_time'])
    end_time = parse_dt(new_class['end_time'])

    for existing in existing_classes:
        existing_start = parse_dt(existing['start_time'])
        existing_end = parse_dt(existing['end_time'])

        # 1. Конфликт по залу
        if new_class['room_id'] == existing['room_id']:
            if intervals_overlap(start_time, end_time, existing_start, existing_end):
                return f"Room conflict: room {existing['room_id']} is already booked"

        # 2. Конфликт по тренеру
        if new_class['trainer_id'] == existing['trainer_id']:
            if intervals_overlap(start_time, end_time, existing_start, existing_end):
                return f"Trainer conflict: trainer {existing['trainer_id']} is already teaching"

    return None


def generate_auto_schedule(data: dict, start_date: datetime, days: int = 7) -> list:
    """
    Простой алгоритм: для каждого типа занятия попробовать
    добавить по одному занятию в день в несколько фиксированных слотов.
    """
    schedule = []
    class_types = data['class_types']
    trainers = data['trainers']
    rooms = data['rooms']
    existing_classes = data['scheduled_classes']

    if not class_types or not trainers or not rooms:
        return schedule

    trainer_id = trainers[0]['id']
    room_id = rooms[0]['id']

    time_slots = [10, 14, 18]  # 10:00, 14:00, 18:00

    for class_type in class_types:
        duration = class_type.get('duration_minutes', 60)

        for day in range(days):
            current_date = start_date + timedelta(days=day)

            for hour in time_slots:
                start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                end = start + timedelta(minutes=duration)

                new_class = {
                    'class_type_id': class_type['id'],
                    'trainer_id': trainer_id,
                    'room_id': room_id,
                    'start_time': start.isoformat(),
                    'end_time': end.isoformat(),
                    'max_enrollment': rooms[0].get('capacity', 20),
                    'current_enrollment': 0
                }

                conflict = check_conflicts(new_class, schedule + existing_classes)
                if not conflict:
                    new_class['id'] = len(existing_classes) + len(schedule) + 1
                    schedule.append(new_class)
                    break  # не пытаемся ставить ещё слоты для этого дня

    return schedule


def find_all_conflicts(scheduled_classes: list) -> list:
    """Поиск всех конфликтов в текущем расписании"""
    conflicts = []

    for i, class1 in enumerate(scheduled_classes):
        start1 = parse_dt(class1['start_time'])
        end1 = parse_dt(class1['end_time'])

        for class2 in scheduled_classes[i + 1:]:
            start2 = parse_dt(class2['start_time'])
            end2 = parse_dt(class2['end_time'])

            # конфликт по залу
            if class1['room_id'] == class2['room_id']:
                if intervals_overlap(start1, end1, start2, end2):
                    conflicts.append({
                        'type': 'room_conflict',
                        'class1_id': class1['id'],
                        'class2_id': class2['id'],
                        'room_id': class1['room_id']
                    })

            # конфликт по тренеру
            if class1['trainer_id'] == class2['trainer_id']:
                if intervals_overlap(start1, end1, start2, end2):
                    conflicts.append({
                        'type': 'trainer_conflict',
                        'class1_id': class1['id'],
                        'class2_id': class2['id'],
                        'trainer_id': class1['trainer_id']
                    })

    return conflicts


def calc_analytics(data: dict) -> dict:
    """Простая статистика по системе"""
    scheduled_classes = data['scheduled_classes']
    total_classes = len(scheduled_classes)
    total_enrollment = sum(sc['current_enrollment'] for sc in scheduled_classes)

    average_enrollment = total_enrollment / total_classes if total_classes else 0

    return {
        'total_trainers': len(data['trainers']),
        'total_rooms': len(data['rooms']),
        'total_classes': total_classes,
        'total_clients': len(data['clients']),
        'total_enrollments': len(data['enrollments']),
        'average_enrollment': round(average_enrollment, 2)
    }
