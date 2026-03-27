from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.documents_home, name='home'),

    # Pastas
    path('pasta/criar/', views.folder_create, name='folder_create'),
    path('pasta/<int:pk>/deletar/', views.folder_delete, name='folder_delete'),

    # Documentos
    path('novo/arquivo/', views.document_upload, name='upload'),
    path('novo/nota/', views.document_note, name='note'),
    path('novo/link/', views.document_link, name='link'),
    path('<int:pk>/', views.document_detail, name='detail'),
    path('<int:pk>/editar/', views.document_edit, name='edit'),
    path('<int:pk>/deletar/', views.document_delete, name='delete'),
    path('<int:pk>/favorito/', views.document_favorite, name='favorite'),

    # Tags
    path('tags/criar/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/deletar/', views.tag_delete, name='tag_delete'),
]