from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('webhook/resend/', views.resend_webhook, name='resend_webhook'),
]