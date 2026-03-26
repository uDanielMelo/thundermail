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
]