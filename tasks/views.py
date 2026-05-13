from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import TaskFilter
from .models import Priority, Project, ProjectMember, Task, TaskComment
from .serializers import (
    PrioritySerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
    TaskCommentSerializer,
    TaskSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


User = get_user_model()


class UserRegistrationView(CreateAPIView):
    # Регистрация открыта без авторизации.
    # Иначе новый пользователь не сможет войти.
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    # Пользователи нужны для назначения задач.
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class PriorityViewSet(viewsets.ModelViewSet):
    # Сначала создаём приоритет.
    # Потом выбираем его id в задаче.
    queryset = Priority.objects.all()
    serializer_class = PrioritySerializer
    permission_classes = [IsAuthenticated]


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Project.objects.none()

        # Пользователь видит только свои проекты.
        return Project.objects.filter(
            members=user,
        ).distinct()

    def perform_update(self, serializer):
        project = self.get_object()

        # Изменять проект может только создатель.
        if project.creator_id != self.request.user.id:
            raise PermissionDenied(
                'Проект редактирует только '
                'его создатель.'
            )

        serializer.save()

    def perform_destroy(self, instance):
        # Удаляет проект только создатель.
        if instance.creator_id != self.request.user.id:
            raise PermissionDenied(
                'Проект удаляет только его создатель.'
            )

        instance.delete()


class ProjectMemberViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return ProjectMember.objects.none()

        # Показываем участников своих проектов.
        return ProjectMember.objects.filter(
            project__members=user,
        ).distinct()

    def perform_create(self, serializer):
        project = serializer.validated_data['project']

        # Участников добавляет только создатель.
        if project.creator_id != self.request.user.id:
            raise PermissionDenied(
                'Участников добавляет только '
                'создатель проекта.'
            )

        serializer.save()

    def perform_destroy(self, instance):
        project = instance.project

        # Участников удаляет только создатель.
        if project.creator_id != self.request.user.id:
            raise PermissionDenied(
                'Участников удаляет только '
                'создатель проекта.'
            )

        # Создатель всегда остаётся в своём проекте.
        if instance.user_id == project.creator_id:
            raise PermissionDenied(
                'Создателя нельзя удалить из проекта.'
            )

        instance.delete()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TaskFilter
    filter_backends = [DjangoFilterBackend]
    
    @action(detail=False, methods=['get'])
    def grouped_by_status(self, request):
        tasks = self.get_queryset()

        result = {
            'todo': [],
            'in_progress': [],
            'review': [],
            'done': [],
        }

        for task in tasks:
            serializer = self.get_serializer(task)
            result[task.status].append(serializer.data)

        return Response(result)

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Task.objects.none()

        # Чужие задачи не попадают в queryset.
        return Task.objects.filter(
            project__members=user,
        ).distinct()

    def perform_create(self, serializer):
        # Автором становится текущий пользователь.
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        self._check_task_update_fields(request)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._check_task_update_fields(request)
        return super().partial_update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        user = self.request.user
        is_project_owner = instance.project.creator_id == user.id
        is_author = instance.author_id == user.id

        # Задачу удаляет владелец проекта или автор.
        if not is_project_owner and not is_author:
            raise PermissionDenied(
                'Задачу удаляет владелец проекта '
                'или автор.'
            )

        instance.delete()

    def _check_task_update_fields(self, request):
        task = self.get_object()
        user = request.user
        fields = set(request.data.keys())

        # Владелец проекта может менять всю задачу.
        if task.project.creator_id == user.id:
            return

        allowed_fields = set()

        # Исполнитель меняет статус и приоритет.
        if task.assignee_id == user.id:
            allowed_fields.update({'status', 'priority'})

        # Автор может уточнить описание задачи.
        if task.author_id == user.id:
            allowed_fields.add('description')

        if allowed_fields:
            self._check_only_allowed_fields(
                fields,
                allowed_fields,
                'В этой роли нельзя менять эти поля.',
            )
            return

        raise PermissionDenied(
            'У вас нет прав на изменение этой задачи.'
        )

    @staticmethod
    def _check_only_allowed_fields(fields, allowed_fields, message):
        forbidden_fields = fields - allowed_fields

        # Лишнее поле запрещает весь запрос.
        if forbidden_fields:
            raise PermissionDenied(message)


class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return TaskComment.objects.none()

        # Комментарии доступны в своих проектах.
        return TaskComment.objects.filter(
            task__project__members=user,
        ).distinct()

    def perform_create(self, serializer):
        # Автор комментария ставится автоматически.
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        comment = self.get_object()
        self._check_comment_owner(comment)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_comment_owner(instance)
        instance.delete()

    def _check_comment_owner(self, comment):
        user = self.request.user
        is_author = comment.author_id == user.id
        is_project_owner = comment.task.project.creator_id == user.id

        # Комментарий правит автор или владелец.
        if not is_author and not is_project_owner:
            raise PermissionDenied(
                'Комментарий меняет автор '
                'или создатель проекта.'
            )
