from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.tasks_home, name='home'),
    path('projeto/criar/', views.project_create, name='project_create'),
    path('projeto/<int:pk>/deletar/', views.project_delete, name='project_delete'),
    path('projeto/<int:pk>/', views.project_detail, name='project_detail'),
    path('tarefa/criar/', views.task_create, name='task_create'),
    path('tarefa/<int:pk>/status/', views.task_update_status, name='task_update_status'),
    path('tarefa/<int:pk>/deletar/', views.task_delete, name='task_delete'),
    path('tarefa/<int:pk>/comentar/', views.task_comment, name='task_comment'),
    path('tarefa/<int:pk>/', views.task_detail, name='task_detail'),
]