import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Integration
from .services.google_analytics import get_flow


@login_required
def integrations_home(request):
    from apps.accounts.models import UserSettings
    integrations = Integration.objects.filter(user=request.user)
    connected = {i.platform: i for i in integrations}
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    return render(request, 'integrations/home.html', {
        'connected': connected,
        'settings': settings_obj,
    })


@login_required
def google_connect(request):
    import secrets
    import hashlib
    import base64

    # Gera code_verifier e code_challenge (PKCE)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        code_challenge=code_challenge,
        code_challenge_method='S256',
    )

    request.session['google_oauth_state'] = state
    request.session['google_code_verifier'] = code_verifier
    return redirect(auth_url)


@login_required
def google_callback(request):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    state = request.session.get('google_oauth_state')
    code_verifier = request.session.get('google_code_verifier')
    platform = request.session.get('google_oauth_platform', 'google_analytics')

    flow = get_flow()
    flow.state = state

    try:
        flow.fetch_token(
            authorization_response=request.build_absolute_uri(),
            code_verifier=code_verifier,
        )
    except Exception as e:
        messages.error(request, f'Erro ao conectar: {str(e)}')
        return redirect('integrations:home')

    credentials = flow.credentials

    Integration.objects.update_or_create(
        user=request.user,
        platform=platform,
        defaults={
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token or '',
            'token_expires_at': credentials.expiry,
            'is_active': True,
            'last_sync_at': timezone.now(),
            'metadata': {},
        }
    )

    if platform == 'youtube':
        messages.success(request, 'YouTube conectado com sucesso!')
    else:
        messages.success(request, 'Google Analytics conectado! Agora informe o ID da propriedade.')

    return redirect('integrations:home')


@login_required
def google_disconnect(request):
    if request.method == 'POST':
        Integration.objects.filter(
            user=request.user,
            platform='google_analytics'
        ).delete()
        messages.success(request, 'Google Analytics desconectado.')
    return redirect('integrations:home')


@login_required
def google_property(request):
    if request.method == 'POST':
        property_id = request.POST.get('property_id', '').strip()
        integration = Integration.objects.filter(
            user=request.user,
            platform='google_analytics'
        ).first()

        if integration and property_id:
            integration.metadata['property_id'] = property_id
            integration.save()
            messages.success(request, 'ID da propriedade salvo com sucesso!')
        else:
            messages.error(request, 'Integração não encontrada ou ID inválido.')

    return redirect('integrations:home')

@login_required
def youtube_connect(request):
    import secrets
    import hashlib
    import base64

    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        code_challenge=code_challenge,
        code_challenge_method='S256',
    )

    request.session['google_oauth_state'] = state
    request.session['google_code_verifier'] = code_verifier
    request.session['google_oauth_platform'] = 'youtube'
    return redirect(auth_url)


@login_required
def youtube_disconnect(request):
    if request.method == 'POST':
        Integration.objects.filter(
            user=request.user,
            platform='youtube'
        ).delete()
        messages.success(request, 'YouTube desconectado.')
    return redirect('integrations:home')    