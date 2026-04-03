from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.billing_list, name='list'),
    path('nova/', views.billing_create, name='create'),
    path('<int:pk>/', views.billing_detail, name='detail'),
    path('webhook/', views.billing_webhook, name='webhook'),
]