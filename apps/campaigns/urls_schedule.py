from django.urls import path
from . import views_schedule

app_name = 'schedule'

urlpatterns = [
    path('', views_schedule.schedule_list, name='list'),
    path('<int:pk>/cancelar/', views_schedule.schedule_cancel, name='cancel'),
    path('agendar/<int:pk>/', views_schedule.schedule_campaign, name='campaign'),
]