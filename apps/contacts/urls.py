from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.contacts_list, name='list'),
    path('grupo/criar/', views.group_create, name='group_create'),
    path('grupo/<int:pk>/deletar/', views.group_delete, name='group_delete'),
    path('importar/csv/', views.import_csv, name='import_csv'),

    # Unsubscribe (público, sem login)
    path('unsubscribe/<uuid:token>/', views.unsubscribe_confirm, name='unsubscribe'),
    path('unsubscribe/<uuid:token>/confirmar/', views.unsubscribe_do, name='unsubscribe_do'),
]