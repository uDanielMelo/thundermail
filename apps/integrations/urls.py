from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('', views.integrations_home, name='home'),
    path('google/connect/', views.google_connect, name='google_connect'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('google/disconnect/', views.google_disconnect, name='google_disconnect'),
    path('google/property/', views.google_property, name='google_property'),
    path('youtube/connect/', views.youtube_connect, name='youtube_connect'),
    path('youtube/disconnect/', views.youtube_disconnect, name='youtube_disconnect'),
]