from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.contacts_list, name='list'),
    path('grupo/criar/', views.group_create, name='group_create'),
    path('grupo/<int:pk>/deletar/', views.group_delete, name='group_delete'),
]