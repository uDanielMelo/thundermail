from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from .middleware import get_user_organization


def cadastro(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'pf')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        nome = request.POST.get('nome', '')

        if password != password2:
            messages.error(request, 'As senhas nao coincidem.')
            return render(request, 'accounts/cadastro.html', {'tipo': tipo})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'E-mail ja cadastrado.')
            return render(request, 'accounts/cadastro.html', {'tipo': tipo})

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=nome,
            telefone=request.POST.get('telefone', ''),
        )

        from .models import Organization, OrganizationMember
        if tipo == 'pf':
            org = Organization.objects.create(
                nome=nome,
                tipo='pf',
                cpf=request.POST.get('cpf', ''),
                telefone=request.POST.get('telefone', ''),
                email=email,
                cep=request.POST.get('cep', ''),
                logradouro=request.POST.get('logradouro', ''),
                numero=request.POST.get('numero', ''),
                complemento=request.POST.get('complemento', ''),
                bairro=request.POST.get('bairro', ''),
                cidade=request.POST.get('cidade', ''),
                estado=request.POST.get('estado', ''),
            )
        else:
            org = Organization.objects.create(
                nome=request.POST.get('razao_social', ''),
                tipo='pj',
                cnpj=request.POST.get('cnpj', ''),
                razao_social=request.POST.get('razao_social', ''),
                nome_fantasia=request.POST.get('nome_fantasia', ''),
                telefone=request.POST.get('telefone', ''),
                email=email,
                cep=request.POST.get('cep', ''),
                logradouro=request.POST.get('logradouro', ''),
                numero=request.POST.get('numero', ''),
                complemento=request.POST.get('complemento', ''),
                bairro=request.POST.get('bairro', ''),
                cidade=request.POST.get('cidade', ''),
                estado=request.POST.get('estado', ''),
            )

        OrganizationMember.objects.create(
            organization=org,
            user=user,
            role='admin',
            status='active'
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

    org = get_user_organization(request.user)

    total_campaigns = Campaign.objects.filter(organization=org).count()
    total_contacts = Contact.objects.filter(organization=org).count()
    total_sent = Campaign.objects.filter(organization=org, status='concluida').count()
    recent_campaigns = Campaign.objects.filter(organization=org)[:5]

    total_finished = Campaign.objects.filter(organization=org, status__in=['concluida', 'erro']).count()
    success_rate = round((total_sent / total_finished * 100), 1) if total_finished > 0 else 0

    context = {
        'total_campaigns': total_campaigns,
        'total_contacts': total_contacts,
        'total_sent': total_sent,
        'recent_campaigns': recent_campaigns,
        'success_rate': success_rate,
    }
    return render(request, 'dashboard.html', context)


@login_required
def configuracoes(request):
    from .models import UserSettings, OrganizationMember, Invite
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    org = get_user_organization(request.user)

    if request.method == 'POST':
        settings_obj.resend_api_key = request.POST.get('resend_api_key', '')
        settings_obj.resend_from_email = request.POST.get('resend_from_email', '')
        settings_obj.twilio_account_sid = request.POST.get('twilio_account_sid', '')
        settings_obj.twilio_auth_token = request.POST.get('twilio_auth_token', '')
        settings_obj.twilio_phone_number = request.POST.get('twilio_phone_number', '')
        settings_obj.save()
        messages.success(request, 'Configuracoes salvas com sucesso!')
        return redirect('accounts:configuracoes')

    members = OrganizationMember.objects.filter(
        organization=org
    ).select_related('user').order_by('role', 'created_at')

    pending_invites = Invite.objects.filter(
        organization=org,
        accepted=False
    ).order_by('-created_at')

    membership = request.user.memberships.filter(status='active').first()
    is_admin = membership.role == 'admin' if membership else False

    return render(request, 'accounts/configuracoes.html', {
        'settings': settings_obj,
        'members': members,
        'pending_invites': pending_invites,
        'org': org,
        'is_admin': is_admin,
    })


@login_required
def perfil(request):
    org = get_user_organization(request.user)
    membership = request.user.memberships.filter(status='active').first()
    is_admin = membership.role == 'admin' if membership else False

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('nome', '')
        user.telefone = request.POST.get('telefone', '')
        user.save()

        # Só admin pode editar dados da organização
        if is_admin and org:
            org.telefone = request.POST.get('telefone', '')
            org.cep = request.POST.get('cep', '')
            org.logradouro = request.POST.get('logradouro', '')
            org.numero = request.POST.get('numero', '')
            org.complemento = request.POST.get('complemento', '')
            org.bairro = request.POST.get('bairro', '')
            org.cidade = request.POST.get('cidade', '')
            org.estado = request.POST.get('estado', '')
            if org.tipo == 'pf':
                org.cpf = request.POST.get('cpf', '')
            else:
                org.cnpj = request.POST.get('cnpj', '')
                org.razao_social = request.POST.get('razao_social', '')
                org.nome_fantasia = request.POST.get('nome_fantasia', '')
            org.save()

        nova_senha = request.POST.get('nova_senha', '')
        senha_atual = request.POST.get('senha_atual', '')
        if nova_senha:
            if not user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta.')
                return render(request, 'accounts/configuracoes.html', {
                    'is_admin': is_admin,
                    'org': org,
                })
            user.set_password(nova_senha)
            user.save()
            messages.success(request, 'Senha alterada! Faca o login novamente.')
            return redirect('accounts:login')

        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('accounts:configuracoes')

    return render(request, 'accounts/configuracoes.html', {
        'is_admin': is_admin,
        'org': org,
    })

@login_required
def membros(request):
    from .models import OrganizationMember, Invite
    org = get_user_organization(request.user)
    members = OrganizationMember.objects.filter(
        organization=org
    ).select_related('user').order_by('role', 'created_at')
    pending_invites = Invite.objects.filter(
        organization=org,
        accepted=False
    ).order_by('-created_at')

    return render(request, 'accounts/membros.html', {
        'members': members,
        'pending_invites': pending_invites,
        'org': org,
    })


@login_required
def convidar_membro(request):
    from .models import Invite, OrganizationMember
    from django.utils import timezone
    import uuid

    org = get_user_organization(request.user)

    if not request.user.is_admin():
        messages.error(request, 'Apenas administradores podem convidar membros.')
        return redirect('accounts:membros')

    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role', 'member')

        if not email:
            messages.error(request, 'Informe o e-mail do convidado.')
            return redirect('accounts:membros')

        if Invite.objects.filter(organization=org, email=email, accepted=False).exists():
            messages.error(request, 'Ja existe um convite pendente para esse e-mail.')
            return redirect('accounts:membros')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if OrganizationMember.objects.filter(organization=org, user=user).exists():
                messages.error(request, 'Esse usuario ja e membro da organizacao.')
                return redirect('accounts:membros')

        invite = Invite.objects.create(
            organization=org,
            email=email,
            token=uuid.uuid4(),
            role=role,
            created_by=request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )

        invite_url = request.build_absolute_uri(
            f'/accounts/convite/{invite.token}/'
        )

        from apps.mailer.services import send_campaign_email
        send_campaign_email(
            to=[email],
            subject=f'Voce foi convidado para {org.nome} no ThunderMail',
            body=f'''
                <h2>Voce foi convidado!</h2>
                <p><strong>{request.user.first_name or request.user.email}</strong>
                convidou voce para fazer parte de <strong>{org.nome}</strong> no ThunderMail.</p>
                <p><a href="{invite_url}"
                style="background:#111827;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block;margin-top:16px;">
                Aceitar Convite</a></p>
                <p style="color:#666;font-size:12px;">Este convite expira em 7 dias.</p>
            '''
        )

        messages.success(request, f'Convite enviado para {email}!')
        return redirect('accounts:membros')

    return redirect('accounts:membros')


@login_required
def remover_membro(request, pk):
    from .models import OrganizationMember
    org = get_user_organization(request.user)

    if not request.user.is_admin():
        messages.error(request, 'Apenas administradores podem remover membros.')
        return redirect('accounts:membros')

    member = get_object_or_404(OrganizationMember, pk=pk, organization=org)

    if member.user == request.user:
        messages.error(request, 'Voce nao pode remover a si mesmo.')
        return redirect('accounts:membros')

    member.delete()
    messages.success(request, 'Membro removido com sucesso.')
    return redirect('accounts:membros')

@login_required
def salvar_permissoes(request, pk):
    from .models import OrganizationMember, MemberPermission
    org = get_user_organization(request.user)

    if not request.user.is_admin():
        messages.error(request, 'Apenas administradores podem alterar permissoes.')
        return redirect('accounts:configuracoes')

    member = get_object_or_404(OrganizationMember, pk=pk, organization=org)

    if request.method == 'POST':
        permissions, _ = MemberPermission.objects.get_or_create(member=member)
        permissions.email_marketing = request.POST.get('email_marketing') == 'on'
        permissions.sms_marketing = request.POST.get('sms_marketing') == 'on'
        permissions.contacts = request.POST.get('contacts') == 'on'
        permissions.scheduling = request.POST.get('scheduling') == 'on'
        permissions.analytics = request.POST.get('analytics') == 'on'
        permissions.integrations = request.POST.get('integrations') == 'on'
        permissions.save()
        messages.success(request, f'Permissoes de {member.user.email} atualizadas!')

    return redirect('accounts:configuracoes')

def aceitar_convite(request, token):
    from .models import Invite, OrganizationMember
    invite = get_object_or_404(Invite, token=token)

    if not invite.is_valid():
        messages.error(request, 'Este convite expirou ou ja foi utilizado.')
        return redirect('accounts:login')

    if request.method == 'POST':
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        nome = request.POST.get('nome', '')

        if password != password2:
            messages.error(request, 'As senhas nao coincidem.')
            return render(request, 'accounts/aceitar_convite.html', {'invite': invite})

        if User.objects.filter(email=invite.email).exists():
            user = User.objects.get(email=invite.email)
            if nome:
                user.first_name = nome
                user.save()
        else:
            user = User.objects.create_user(
                username=invite.email,
                email=invite.email,
                password=password,
                first_name=nome,
            )

        OrganizationMember.objects.get_or_create(
            organization=invite.organization,
            user=user,
            defaults={'role': invite.role, 'status': 'active'}
        )

        invite.accepted = True
        invite.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Bem-vindo ao {invite.organization.nome}!')
        return redirect('dashboard')

    return render(request, 'accounts/aceitar_convite.html', {'invite': invite})


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')