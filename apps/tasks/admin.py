from django.contrib import admin
from .models import Project, Task, TaskComment

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'total_tasks', 'created_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'due_date', 'assigned_to']
    list_filter = ['status', 'priority', 'project']

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at']