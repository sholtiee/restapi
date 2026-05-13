from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Priority, Project, ProjectMember, Task, TaskComment


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    # Пароль нужен только при создании.
    # В ответе API его быть не должно.
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
        ]

    def create(self, validated_data):
        # create_user хеширует пароль.
        # Пароль не хранится обычным текстом.
        return User.objects.create_user(**validated_data)


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = [
            'id',
            'name',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'creator',
            'members',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'creator',
            'members',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        request = self.context['request']
        # Создатель сразу становится участником.
        project = Project.objects.create(
            creator=request.user,
            **validated_data,
        )
        ProjectMember.objects.create(
            project=project,
            user=request.user,
        )
        return project


class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = [
            'id',
            'project',
            'user',
            'joined_at',
        ]
        read_only_fields = [
            'id',
            'joined_at',
        ]

    def validate(self, attrs):
        project = attrs['project']
        user = attrs['user']

        # Проверяем дубликат до сохранения.
        # Так API вернёт понятную ошибку.
        exists = ProjectMember.objects.filter(
            project=project,
            user=user,
        ).exists()

        if exists:
            raise serializers.ValidationError(
                'Пользователь уже участвует в проекте.'
            )

        return attrs


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'project',
            'title',
            'description',
            'priority',
            'status',
            'deadline',
            'author',
            'assignee',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'author',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        request = self.context['request']
        project = attrs.get('project')
        assignee = attrs.get('assignee')

        if self.instance:
            # Задачу не переносим между проектами.
            old_project = self.instance.project
            project = project or old_project
            assignee = assignee or self.instance.assignee

            if project != old_project:
                raise serializers.ValidationError(
                    'Нельзя переносить задачу '
                    'в другой проект.'
                )

        is_request_user_member = ProjectMember.objects.filter(
            project=project,
            user=request.user,
        ).exists()

        # Нельзя менять задачи в чужом проекте.
        if not is_request_user_member:
            raise serializers.ValidationError(
                'Менять задачи могут только '
                'участники проекта.'
            )

        is_assignee_member = ProjectMember.objects.filter(
            project=project,
            user=assignee,
        ).exists()

        # Исполнитель должен быть участником.
        if not is_assignee_member:
            raise serializers.ValidationError(
                'Исполнитель должен быть '
                'участником проекта.'
            )

        return attrs


class TaskCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = [
            'id',
            'task',
            'author',
            'text',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'author',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        request = self.context['request']
        task = attrs.get('task')

        if self.instance:
            # Комментарий остаётся у своей задачи.
            task = task or self.instance.task

            if task != self.instance.task:
                raise serializers.ValidationError(
                    'Нельзя переносить комментарий '
                    'к другой задаче.'
                )

        is_member = ProjectMember.objects.filter(
            project=task.project,
            user=request.user,
        ).exists()

        # Комментарии пишут только участники.
        if not is_member:
            raise serializers.ValidationError(
                'Комментировать может только '
                'участник проекта.'
            )

        return attrs
