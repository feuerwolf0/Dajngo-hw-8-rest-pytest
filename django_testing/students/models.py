from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import m2m_changed


class Student(models.Model):

    name = models.TextField()

    birth_date = models.DateField(
        null=True,
    )


class Course(models.Model):

    name = models.TextField()

    students = models.ManyToManyField(
        Student,
        blank=True,
    )


# Проверка количества студентов записанных на курс.
def students_changed(sender, **kwargs):
    max_students = settings.MAX_STUDENTS_PER_COURSE
    if kwargs['instance'].students.count() > max_students:
        raise ValidationError(f"Курс заполнен. Максимальное количество студентов: {max_students}")


m2m_changed.connect(students_changed, sender=Course.students.through)