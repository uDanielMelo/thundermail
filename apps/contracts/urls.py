from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('', views.contracts_list, name='list'),
    path('criar/', views.contract_create, name='create'),
    path('<int:pk>/', views.contract_detail, name='detail'),
    path('<int:pk>/enviar/', views.contract_send, name='send'),
    path('<int:pk>/cancelar/', views.contract_cancel, name='cancel'),
    path('<int:pk>/deletar/', views.contract_delete, name='delete'),

    # Assinatura (público, sem login)
    path('assinar/<uuid:token>/', views.sign_view, name='sign'),
    path('assinar/<uuid:token>/confirmar/', views.sign_confirm, name='sign_confirm'),
    path('assinar/<uuid:token>/recusar/', views.sign_decline, name='sign_decline'),
    path('assinar/<uuid:token>/concluido/', views.sign_done, name='sign_done'),
    path('<int:pk>/download/', views.contract_download, name='download'),
]
