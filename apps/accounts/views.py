from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User


def cadastro(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'pf')
        username = request.POST.get('email')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validacoes basicas
        if password != password2:
            messages.error(request, 'As senhas nao coincidem.')
            return render(request, 'accounts/cadastro.html', {'tipo': tipo})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'E-mail ja cadastrado.')
            return render(request, 'accounts/cadastro.html', {'tipo': tipo})

        if tipo == 'pf':
            cpf = request.POST.get('cpf')
            if User.objects.filter(cpf=cpf).exists():
                messages.error(request, 'CPF ja cadastrado.')
                return render(request, 'accounts/cadastro.html', {'tipo': tipo})

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                tipo='pf',
                first_name=request.POST.get('nome', ''),
                cpf=cpf,
                data_nascimento=request.POST.get('data_nascimento') or None,
                telefone=request.POST.get('telefone'),
                cep=request.POST.get('cep'),
                logradouro=request.POST.get('logradouro'),
                numero=request.POST.get('numero'),
                complemento=request.POST.get('complemento'),
                bairro=request.POST.get('bairro'),
                cidade=request.POST.get('cidade'),
                estado=request.POST.get('estado'),
            )
        else:
            cnpj = request.POST.get('cnpj')
            if User.objects.filter(cnpj=cnpj).exists():
                messages.error(request, 'CNPJ ja cadastrado.')
                return render(request, 'accounts/cadastro.html', {'tipo': tipo})

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                tipo='pj',
                razao_social=request.POST.get('razao_social'),
                nome_fantasia=request.POST.get('nome_fantasia'),
                cnpj=cnpj,
                telefone=request.POST.get('telefone'),
                cep=request.POST.get('cep'),
                logradouro=request.POST.get('logradouro'),
                numero=request.POST.get('numero'),
                complemento=request.POST.get('complemento'),
                bairro=request.POST.get('bairro'),
                cidade=request.POST.get('cidade'),
                estado=request.POST.get('estado'),
            )

        messages.success(request, 'Conta criada com sucesso! Faca o login.')
        return redirect('accounts:login')

    return render(request, 'accounts/cadastro.html', {'tipo': 'pf'})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'E-mail ou senha incorretos.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    from apps.campaigns.models import Campaign
    from apps.contacts.models import Contact
    from apps.integrations.models import Integration
    from apps.integrations.services.google_analytics import get_analytics_metrics

    total_campaigns = Campaign.objects.filter(user=request.user).count()
    total_contacts = Contact.objects.filter(user=request.user).count()
    total_sent = Campaign.objects.filter(user=request.user, status='concluida').count()
    recent_campaigns = Campaign.objects.filter(user=request.user)[:5]

    total_finished = Campaign.objects.filter(user=request.user, status__in=['concluida', 'erro']).count()
    success_rate = round((total_sent / total_finished * 100), 1) if total_finished > 0 else 0

    # Métricas do Google Analytics
    ga_metrics = None
    ga_integration = Integration.objects.filter(
        user=request.user,
        platform='google_analytics',
        is_active=True
    ).first()

    if ga_integration and ga_integration.metadata.get('property_id'):
        ga_metrics = get_analytics_metrics(ga_integration)

    context = {
        'total_campaigns': total_campaigns,
        'total_contacts': total_contacts,
        'total_sent': total_sent,
        'recent_campaigns': recent_campaigns,
        'success_rate': success_rate,
        'ga_metrics': ga_metrics,
    }
    return render(request, 'dashboard.html', context)

@login_required
def configuracoes(request):
    from .models import UserSettings
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        settings_obj.resend_api_key = request.POST.get('resend_api_key', '')
        settings_obj.resend_from_email = request.POST.get('resend_from_email', '')
        settings_obj.twilio_account_sid = request.POST.get('twilio_account_sid', '')
        settings_obj.twilio_auth_token = request.POST.get('twilio_auth_token', '')
        settings_obj.twilio_phone_number = request.POST.get('twilio_phone_number', '')
        settings_obj.save()
        messages.success(request, 'Configuracoes salvas com sucesso!')
        return redirect('accounts:configuracoes')

    return render(request, 'accounts/configuracoes.html', {'settings': settings_obj})

@login_required
def perfil(request):
    if request.method == 'POST':
        user = request.user

        user.first_name = request.POST.get('nome', '')
        user.telefone = request.POST.get('telefone', '')
        user.cep = request.POST.get('cep', '')
        user.logradouro = request.POST.get('logradouro', '')
        user.numero = request.POST.get('numero', '')
        user.complemento = request.POST.get('complemento', '')
        user.bairro = request.POST.get('bairro', '')
        user.cidade = request.POST.get('cidade', '')
        user.estado = request.POST.get('estado', '')

        if user.tipo == 'pf':
            user.cpf = request.POST.get('cpf', '')
            user.data_nascimento = request.POST.get('data_nascimento') or None
        else:
            user.cnpj = request.POST.get('cnpj', '')
            user.razao_social = request.POST.get('razao_social', '')
            user.nome_fantasia = request.POST.get('nome_fantasia', '')

        # Troca de senha
        nova_senha = request.POST.get('nova_senha', '')
        senha_atual = request.POST.get('senha_atual', '')
        if nova_senha:
            if not user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta.')
                return render(request, 'accounts/perfil.html', {'user': user})
            user.set_password(nova_senha)
            messages.success(request, 'Senha alterada com sucesso! Faca o login novamente.')
            user.save()
            return redirect('accounts:login')

        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('accounts:perfil')

    return render(request, 'accounts/perfil.html')

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')
    