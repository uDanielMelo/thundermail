from django.contrib import admin
from django.urls import path, include
from apps.accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('contacts/', include('apps.contacts.urls', namespace='contacts')),
    path('dashboard/', accounts_views.dashboard, name='dashboard'),
]