from django.db import models
from django.conf import settings
from apps.accounts.models import Organization


class Project(models.Model):
    COLOR_CHOICES = [
        ('#378ADD', 'Azul'),
        ('#1D9E75', 'Verde'),
        ('#D85A30', 'Laranja'),
        ('#7F77DD', 'Roxo'),
        ('#D4537E', 'Rosa'),
        ('#888780', 'Cinza'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='#378ADD')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def __str__(self):
        return self.name

    @property
    def total_tasks(self):
        return self.tasks.count()

    @property
    def open_tasks(self):
        return self.tasks.exclude(status='done').count()


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'A fazer'),
        ('doing', 'Em andamento'),
        ('done', 'Concluído'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'

    def __str__(self):
        return f'Comentário de {self.user.email} em {self.task.title}'