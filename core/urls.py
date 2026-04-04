from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.accounts import views as accounts_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.index, name='index'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('contacts/', include('apps.contacts.urls', namespace='contacts')),
    path('campaigns/', include('apps.campaigns.urls', namespace='campaigns')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('dashboard/', accounts_views.dashboard, name='dashboard'),
    path('agendamentos/', include('apps.campaigns.urls_schedule', namespace='schedule')),
    path('integrations/', include('apps.integrations.urls', namespace='integrations')),
    path('contracts/', include('apps.contracts.urls', namespace='contracts')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('billing/', include('apps.billing.urls', namespace='billing')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),

    # Reset de senha
    path('accounts/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            html_email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/accounts/password-reset/done/'
        ),
        name='password_reset'),

    path('accounts/password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'),

    path('accounts/password-reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/accounts/password-reset/complete/'
        ),
        name='password_reset_confirm'),

    path('accounts/password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)