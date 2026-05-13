import django_filters

from .models import Task


class TaskFilter(django_filters.FilterSet):
    # Фильтры повторяют основные поля задачи.
    project = django_filters.NumberFilter(field_name='project_id')
    status = django_filters.ChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.NumberFilter(field_name='priority_id')
    assignee = django_filters.NumberFilter(field_name='assignee_id')
    deadline = django_filters.DateFilter(field_name='deadline')
    # Фильтры по периоду.
    deadline_after = django_filters.DateFilter(
        field_name='deadline',
        lookup_expr='gte',
    )
    deadline_before = django_filters.DateFilter(
        field_name='deadline',
        lookup_expr='lte',
    )

    class Meta:
        model = Task
        fields = [
            'project',
            'status',
            'priority',
            'assignee',
            'deadline',
            'deadline_after',
            'deadline_before',
        ]
