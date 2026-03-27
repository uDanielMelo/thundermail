from django.contrib import admin
from django.urls import path, include
from apps.accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.index, name='index'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('contacts/', include('apps.contacts.urls', namespace='contacts')),
    path('campaigns/', include('apps.campaigns.urls', namespace='campaigns')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('dashboard/', accounts_views.dashboard, name='dashboard'),
    path('agendamentos/', include('apps.campaigns.urls_schedule', namespace='schedule')),
    path('integrations/', include('apps.integrations.urls', namespace='integrations')),  # ← nova linha
]