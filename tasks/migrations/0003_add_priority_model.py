import django.db.models.deletion
from django.db import migrations, models


def fill_priorities(apps, schema_editor):
    Priority = apps.get_model('tasks', 'Priority')
    Task = apps.get_model('tasks', 'Task')

    priority_names = {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий',
        'urgent': 'Срочный',
    }

    priorities = {}
    for old_value, name in priority_names.items():
        priority, _ = Priority.objects.get_or_create(name=name)
        priorities[old_value] = priority

    default_priority = priorities['medium']

    for task in Task.objects.all():
        task.priority = priorities.get(task.old_priority, default_priority)
        task.save(update_fields=['priority'])


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_remove_task_tasks_task_project_b78682_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Priority',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'name',
                    models.CharField(
                        max_length=50,
                        unique=True,
                        verbose_name='Название',
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name='Дата создания',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Приоритет',
                'verbose_name_plural': 'Приоритеты',
                'ordering': ['id'],
            },
        ),
        migrations.RenameField(
            model_name='task',
            old_name='priority',
            new_name='old_priority',
        ),
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tasks',
                to='tasks.priority',
                verbose_name='Приоритет',
            ),
        ),
        migrations.RunPython(
            fill_priorities,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='task',
            name='priority',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tasks',
                to='tasks.priority',
                verbose_name='Приоритет',
            ),
        ),
        migrations.RemoveField(
            model_name='task',
            name='old_priority',
        ),
    ]
