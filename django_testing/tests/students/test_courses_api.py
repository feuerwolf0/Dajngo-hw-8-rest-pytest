import pytest
from django.conf import settings
from django.contrib.auth.models import User
from model_bakery import baker
from rest_framework.test import APIClient

from students.models import Course, Student


@pytest.fixture
def admin():
    return User.objects.create_user(username='Admin')


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def course_factory():
    def factory(*args, **kwargs):
        return baker.make(Course, make_m2m=True, *args, **kwargs)

    return factory


@pytest.fixture
def student_factory():
    def factory(*args, **kwargs):
        return baker.make(Student, *args, **kwargs)

    return factory


@pytest.fixture
def max_students():
    return settings.MAX_STUDENTS_PER_COURSE


# Тест получения одного курса
@pytest.mark.django_db
def test_retrieve_course(client, course_factory, student_factory):
    # Создаю 3х студентов
    students = student_factory(_quantity=3)
    # Создаю курс с 3я студентами
    course = course_factory(_quantity=1, students=students)

    course_id = course[0].id
    response = client.get(f'/api/v1/courses/{course_id}/')
    data = response.json()
    students_m2m_ids = [student.id for student in course[0].students.all()]

    assert response.status_code == 200
    assert course[0].id == data['id']
    assert course[0].name == data['name']
    assert students_m2m_ids == data['students']


# Тест получения полного списка курсов
@pytest.mark.django_db
def test_list_course(client, course_factory, student_factory):
    students1 = student_factory(_quantity=7)
    courses = course_factory(_quantity=12, students=students1)

    response = client.get('/api/v1/courses/')
    data = response.json()
    students_m2m_ids = [student.id for student in courses[0].students.all()]


    assert response.status_code == 200
    assert len(data) == 12

    for i in range(len(data)):
        assert data[i]['id'] == courses[i].id
        assert data[i]['name'] == courses[i].name
        assert data[i]['students'] == students_m2m_ids


# Тест поиска курса по его ID
@pytest.mark.django_db
def test_filtering_by_course_id(client, course_factory, student_factory):
    students = student_factory(_quantity=3)
    courses = course_factory(_quantity=23, students=students)
    # Получаю список студентов для поля 'students'
    students_m2m_ids = [student.id for student in courses[0].students.all()]

    #Выбираю id который хочу найти
    course_id = courses[3].id
    # Получаю объект с таким id для сравнения
    course_obj = Course.objects.get(id=course_id)

    response = client.get('/api/v1/courses/', {'id': course_id})
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]['id'] == int(course_id)
    assert data[0]['name'] == course_obj.name
    assert data[0]['students'] == students_m2m_ids


# Тест поиска курса по его названию
@pytest.mark.django_db
def test_filtering_by_course_name(client, course_factory, student_factory):
    students = student_factory(_quantity=5)
    courses = course_factory(_quantity=41, students=students)
    # Получаю список студентов для поля 'students'
    students_m2m_ids = [student.id for student in courses[0].students.all()]

    # Выбираю name для поиска
    course_name = courses[13].name
    course_obj = Course.objects.get(name=course_name)

    response = client.get('/api/v1/courses/', {'name': course_name})
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]['id'] == course_obj.id
    assert data[0]['name'] == course_obj.name
    assert data[0]['students'] == students_m2m_ids


# Тест создания курса с использованием метода POST
@pytest.mark.django_db
def test_create_course_using_post(client):
    course_json = {
        'name': 'Just another course',
    }

    response = client.post('/api/v1/courses/', data=course_json, format='json')
    course_id = response.data.get('id')

    response_before_creating = client.get(f'/api/v1/courses/{course_id}/')

    assert response.status_code == 201
    assert response.data['name'] == 'Just another course'
    assert response_before_creating.status_code == 200
    assert response_before_creating.data['name'] == 'Just another course'


# Тест обновления курса с использованием метода PUT
@pytest.mark.django_db
def test_update_course_using_put(client, course_factory):
    course = course_factory()
    course_id = course.id

    update_json = {
        'name': 'Updated course name'
    }

    response = client.put(f'/api/v1/courses/{course_id}/', data=update_json, format='json')

    assert response.status_code == 200
    assert response.data['id'] == course_id
    assert response.data['name'] == 'Updated course name'


# Тест удаление курса с использованием метода DELETE
@pytest.mark.django_db
def test_delete_course_using_delete(client, course_factory):
    course = course_factory()
    course_id = course.id

    response_before_delete = client.get(f'/api/v1/courses/{course_id}/')

    response = client.delete(f'/api/v1/courses/{course_id}/')

    response_after_delete = client.get(f'/api/v1/courses/{course_id}/')

    #Проверяю что курс существует
    assert response_before_delete.status_code == 200
    # Проверяю удаление курса
    assert response.status_code == 204
    assert response.data == None
    # Проверяю что курса более не существует
    assert response_after_delete.status_code == 404


# Тест на максимальное количество студентов на курсе.
# Владация-ограничение прописана в models.py
# Данная функция тестирует значение максимального количества студентов на курсе указанного в настройках
@pytest.mark.parametrize('max_count', [0, 8, 10, 20, 19, 9])
def test_valid_max_students_per_course(max_students, max_count):
    assert max_students >= max_count, 'Количество студентов на курсе должно быть меньше или равно 20'


@pytest.mark.parametrize('max_count', [33, 130, 21, 22, 26])
def test_invalid_max_students_per_course(max_students, max_count):
    assert max_students < max_count, 'Количество студентов на курсе должно быть меньше или равно 20'


