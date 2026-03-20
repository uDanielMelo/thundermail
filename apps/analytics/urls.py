from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('campanha/<int:pk>/', views.campaign_analytics, name='campaign'),
]