from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('perfil/', views.perfil, name='perfil'),
    path('membros/', views.membros, name='membros'),
    path('membros/convidar/', views.convidar_membro, name='convidar_membro'),
    path('membros/<int:pk>/remover/', views.remover_membro, name='remover_membro'),
    path('convite/<uuid:token>/', views.aceitar_convite, name='aceitar_convite'),
    path('membros/<int:pk>/permissoes/', views.salvar_permissoes, name='salvar_permissoes'),
]