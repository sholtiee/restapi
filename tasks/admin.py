from django.contrib import admin

from .models import Priority, Project, ProjectMember, Task, TaskComment


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'creator', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    inlines = (ProjectMemberInline,)


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'user', 'joined_at')
    search_fields = ('project__name', 'user__username')


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'project',
        'status',
        'priority',
        'assignee',
        'deadline',
    )
    search_fields = ('title', 'description')
    list_filter = ('status', 'priority', 'deadline')


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'created_at')
    search_fields = ('text', 'task__title', 'author__username')
