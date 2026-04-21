from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.campaigns_list, name='list'),
    path('criar/', views.campaign_create, name='create'),
    path('<int:pk>/', views.campaign_detail, name='detail'),
    path('<int:pk>/deletar/', views.campaign_delete, name='delete'),
    path('<int:pk>/editar/', views.campaign_edit, name='edit'),
    path('<int:pk>/duplicar/', views.campaign_duplicate, name='duplicate'),
path('<int:pk>/enviar/', views.campaign_send_now, name='send_now'),
    path('<int:pk>/status/', views.campaign_send_status, name='send_status'),
    path('templates/salvar/', views.template_save, name='template_save'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/<int:pk>/deletar/', views.template_delete, name='template_delete'),
]