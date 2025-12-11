import pytest
from app import app
from logic import check_conflicts


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'


def test_check_conflict_room():
    new_class = {
        'room_id': 1,
        'trainer_id': 1,
        'start_time': '2024-12-12T10:00:00',
        'end_time': '2024-12-12T11:00:00'
    }
    existing = {
        'room_id': 1,
        'trainer_id': 2,
        'start_time': '2024-12-12T10:30:00',
        'end_time': '2024-12-12T11:30:00'
    }
    conflict = check_conflicts(new_class, [existing])
    assert conflict is not None
    assert 'Room conflict' in conflict


def test_check_conflict_none():
    new_class = {
        'room_id': 1,
        'trainer_id': 1,
        'start_time': '2024-12-12T10:00:00',
        'end_time': '2024-12-12T11:00:00'
    }
    existing = {
        'room_id': 1,
        'trainer_id': 2,
        'start_time': '2024-12-12T11:00:00',
        'end_time': '2024-12-12T12:00:00'
    }
    conflict = check_conflicts(new_class, [existing])
    assert conflict is None
