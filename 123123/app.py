from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
)
from datetime import datetime, timedelta
from functools import wraps

from storage import data, save_data
from logic import (
    check_conflicts,
    generate_auto_schedule,
    find_all_conflicts,
    calc_analytics,
)

app = Flask(__name__)
app.secret_key = 'your_secret_key_12345'


# ---------- ДЕКОРАТОР ДЛЯ ПРОВЕРКИ ПАРОЛЯ ----------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------- ЛОГИН ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        print(f'Полученный пароль: "{password}"')
        if password == '123123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            print(f'Пароль неверный')
            return render_template('login.html', error='Неверный пароль')
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


# ---------- ГЛАВНАЯ СТРАНИЦА ----------

@app.route('/', methods=['GET'])
def root():
    return '<h1>Добро пожаловать</h1><p>Войти как Администратор: <a href="/web">/web</a><br>Войти как Клиент: <a href="/web2">/web2</a></p>'


# ---------- АДМИН-ПАНЕЛЬ /web (с паролем) ----------

@app.route('/web', methods=['GET'])
@login_required
def index():
    return render_template(
        'index.html',
        trainers=data['trainers'],
        rooms=data['rooms'],
        class_types=data['class_types'],
        clients=data['clients'],
        scheduled_classes=data['scheduled_classes'],
    )


@app.route('/web/add_trainer', methods=['POST'])
@login_required
def web_add_trainer():
    name = request.form.get('name')
    specialization = request.form.get('specialization', '')
    if not name:
        return redirect(url_for('index'))

    trainer = {
        'id': len(data['trainers']) + 1,
        'name': name,
        'specialization': specialization,
        'max_classes_per_day': 6,
    }
    data['trainers'].append(trainer)
    save_data()
    return redirect(url_for('index'))


@app.route('/web/add_room', methods=['POST'])
@login_required
def web_add_room():
    name = request.form.get('name')
    capacity = request.form.get('capacity', '0')
    if not name:
        return redirect(url_for('index'))

    room = {
        'id': len(data['rooms']) + 1,
        'name': name,
        'capacity': int(capacity) if capacity.isdigit() else 0,
    }
    data['rooms'].append(room)
    save_data()
    return redirect(url_for('index'))


@app.route('/web/add_class_type', methods=['POST'])
@login_required
def web_add_class_type():
    name = request.form.get('name')
    duration = request.form.get('duration', '60')
    if not name:
        return redirect(url_for('index'))

    class_type = {
        'id': len(data['class_types']) + 1,
        'name': name,
        'duration_minutes': int(duration) if duration.isdigit() else 60,
    }
    data['class_types'].append(class_type)
    save_data()
    return redirect(url_for('index'))


@app.route('/web/add_client', methods=['POST'])
@login_required
def web_add_client():
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        return redirect(url_for('index'))

    client = {
        'id': len(data['clients']) + 1,
        'name': name,
        'email': email,
    }
    data['clients'].append(client)
    save_data()
    return redirect(url_for('index'))


@app.route('/web/add_scheduled_class', methods=['POST'])
@login_required
def web_add_scheduled_class():
    class_type_id = request.form.get('class_type_id')
    trainer_id = request.form.get('trainer_id')
    room_id = request.form.get('room_id')
    date = request.form.get('date')
    start_time = request.form.get('start_time')
    duration = request.form.get('duration', '60')
    max_enrollment = request.form.get('max_enrollment', '20')

    if not (class_type_id and trainer_id and room_id and date and start_time):
        return redirect(url_for('index'))

    start_dt = datetime.fromisoformat(f'{date}T{start_time}')
    end_dt = start_dt + timedelta(minutes=int(duration))

    new_class = {
        'class_type_id': int(class_type_id),
        'trainer_id': int(trainer_id),
        'room_id': int(room_id),
        'start_time': start_dt.isoformat(),
        'end_time': end_dt.isoformat(),
        'max_enrollment': int(max_enrollment),
        'current_enrollment': 0,
    }

    conflict = check_conflicts(new_class, data['scheduled_classes'])
    if conflict:
        print('CONFLICT:', conflict)
        return redirect(url_for('index'))

    new_class['id'] = len(data['scheduled_classes']) + 1
    data['scheduled_classes'].append(new_class)
    save_data()
    return redirect(url_for('index'))


# ---------- КЛИЕНТСКАЯ ЧАСТЬ /web2 (без пароля) ----------

@app.route('/web2', methods=['GET'])
def client_page():
    return render_template(
        'client.html',
        class_types=data['class_types'],
        trainers=data['trainers'],
        rooms=data['rooms'],
        scheduled_classes=data['scheduled_classes'],
    )


@app.route('/web2/enroll_client', methods=['POST'])
def web2_enroll_client():
    name = request.form.get('name')
    email = request.form.get('email')
    scheduled_class_id = request.form.get('scheduled_class_id')

    if not (name and email and scheduled_class_id):
        return redirect(url_for('client_page'))

    existing_client = next(
        (c for c in data['clients'] if c['email'] == email),
        None
    )
    if existing_client:
        client_id = existing_client['id']
    else:
        client_id = len(data['clients']) + 1
        client = {
            'id': client_id,
            'name': name,
            'email': email,
        }
        data['clients'].append(client)

    scheduled_class = next(
        (sc for sc in data['scheduled_classes']
         if sc['id'] == int(scheduled_class_id)),
        None
    )
    if not scheduled_class:
        return redirect(url_for('client_page'))

    if scheduled_class['current_enrollment'] >= scheduled_class['max_enrollment']:
        return render_template(
            'client.html',
            class_types=data['class_types'],
            trainers=data['trainers'],
            rooms=data['rooms'],
            scheduled_classes=data['scheduled_classes'],
            error='Занятие заполнено',
        )

    enrollment = {
        'id': len(data['enrollments']) + 1,
        'scheduled_class_id': int(scheduled_class_id),
        'client_id': client_id,
        'status': 'enrolled',
    }
    data['enrollments'].append(enrollment)
    scheduled_class['current_enrollment'] += 1
    save_data()

    return render_template(
        'client.html',
        class_types=data['class_types'],
        trainers=data['trainers'],
        rooms=data['rooms'],
        scheduled_classes=data['scheduled_classes'],
        success='Вы успешно записались на занятие!',
    )


# ---------- API ----------

@app.route('/trainers', methods=['GET'])
def get_trainers():
    return jsonify(data['trainers']), 200


@app.route('/trainers', methods=['POST'])
def create_trainer():
    trainer = request.json
    trainer['id'] = len(data['trainers']) + 1
    trainer.setdefault('max_classes_per_day', 6)
    data['trainers'].append(trainer)
    save_data()
    return jsonify(trainer), 201


@app.route('/trainers/<int:trainer_id>', methods=['PUT'])
def update_trainer(trainer_id):
    for trainer in data['trainers']:
        if trainer['id'] == trainer_id:
            trainer.update(request.json)
            save_data()
            return jsonify(trainer), 200
    return {'error': 'Trainer not found'}, 404


@app.route('/rooms', methods=['GET'])
def get_rooms():
    return jsonify(data['rooms']), 200


@app.route('/rooms', methods=['POST'])
def create_room():
    room = request.json
    room['id'] = len(data['rooms']) + 1
    data['rooms'].append(room)
    save_data()
    return jsonify(room), 201


@app.route('/class-types', methods=['GET'])
def get_class_types():
    return jsonify(data['class_types']), 200


@app.route('/class-types', methods=['POST'])
def create_class_type():
    class_type = request.json
    class_type['id'] = len(data['class_types']) + 1
    class_type.setdefault('duration_minutes', 60)
    data['class_types'].append(class_type)
    save_data()
    return jsonify(class_type), 201


@app.route('/clients', methods=['GET'])
def get_clients():
    return jsonify(data['clients']), 200


@app.route('/clients', methods=['POST'])
def create_client():
    client = request.json
    client['id'] = len(data['clients']) + 1
    data['clients'].append(client)
    save_data()
    return jsonify(client), 201


@app.route('/schedule', methods=['GET'])
def get_schedule():
    return jsonify(data['scheduled_classes']), 200


@app.route('/schedule', methods=['POST'])
def create_schedule():
    new_class = request.json

    required_fields = ['class_type_id', 'trainer_id', 'room_id',
                       'start_time', 'end_time', 'max_enrollment']
    missing = [f for f in required_fields if f not in new_class]
    if missing:
        return {'error': f'Missing fields: {", ".join(missing)}'}, 400

    conflict = check_conflicts(new_class, data['scheduled_classes'])
    if conflict:
        return {'error': conflict}, 400

    new_class['id'] = len(data['scheduled_classes']) + 1
    new_class['current_enrollment'] = 0
    data['scheduled_classes'].append(new_class)
    save_data()
    return jsonify(new_class), 201


@app.route('/enroll', methods=['POST'])
def enroll_class():
    enrollment = request.json

    required_fields = ['scheduled_class_id', 'client_id']
    missing = [f for f in required_fields if f not in enrollment]
    if missing:
        return {'error': f'Missing fields: {", ".join(missing)}'}, 400

    scheduled_class = next(
        (sc for sc in data['scheduled_classes']
         if sc['id'] == enrollment['scheduled_class_id']),
        None
    )
    if not scheduled_class:
        return {'error': 'Class not found'}, 404

    if scheduled_class['current_enrollment'] >= scheduled_class['max_enrollment']:
        return {'error': 'Class is full'}, 400

    enrollment['id'] = len(data['enrollments']) + 1
    enrollment['status'] = 'enrolled'
    data['enrollments'].append(enrollment)

    scheduled_class['current_enrollment'] += 1
    save_data()
    return jsonify(enrollment), 201


@app.route('/generate-schedule', methods=['POST'])
def generate_schedule():
    params = request.json or {}
    start_date_str = params.get('start_date')
    days = params.get('days', 7)

    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str)
    else:
        start_date = datetime.now()

    generated = generate_auto_schedule(
        data=data,
        start_date=start_date,
        days=days
    )
    return jsonify({'generated_classes': generated}), 200


@app.route('/conflicts', methods=['GET'])
def conflicts():
    conflicts_list = find_all_conflicts(data['scheduled_classes'])
    return jsonify({'conflicts': conflicts_list}), 200


@app.route('/analytics', methods=['GET'])
def analytics():
    return jsonify(calc_analytics(data)), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)