from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User


def cadastro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        cpf = request.POST.get('cpf')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'accounts/cadastro.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'E-mail já cadastrado.')
            return render(request, 'accounts/cadastro.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            cpf=cpf,
            password=password
        )
        messages.success(request, 'Conta criada com sucesso!')
        return redirect('accounts:login')

    return render(request, 'accounts/cadastro.html')


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

    total_campaigns = Campaign.objects.filter(user=request.user).count()
    total_contacts = Contact.objects.filter(user=request.user).count()
    total_sent = Campaign.objects.filter(user=request.user, status='concluida').count()
    recent_campaigns = Campaign.objects.filter(user=request.user)[:5]

    total_finished = Campaign.objects.filter(user=request.user, status__in=['concluida', 'erro']).count()
    success_rate = round((total_sent / total_finished * 100), 1) if total_finished > 0 else 0

    context = {
        'total_campaigns': total_campaigns,
        'total_contacts': total_contacts,
        'total_sent': total_sent,
        'recent_campaigns': recent_campaigns,
        'success_rate': success_rate,
    }
    return render(request, 'dashboard.html', context)

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')