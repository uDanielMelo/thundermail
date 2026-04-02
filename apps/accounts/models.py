from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.email

    def get_organization(self):
        membership = self.memberships.filter(status='active').first()
        return membership.organization if membership else None

    def is_admin(self):
        membership = self.memberships.filter(status='active').first()
        return membership.role == 'admin' if membership else False


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    # Resend
    resend_api_key = models.CharField(max_length=200, blank=True, null=True)
    resend_from_email = models.EmailField(blank=True, null=True)

    # Twilio
    twilio_account_sid = models.CharField(max_length=100, blank=True, null=True)
    twilio_auth_token = models.CharField(max_length=100, blank=True, null=True)
    twilio_phone_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Configuracoes do Usuario'

    def __str__(self):
        return f'Settings de {self.user.email}'


class Organization(models.Model):
    TIPO_CHOICES = [
        ('pf', 'Pessoa Fisica'),
        ('pj', 'Pessoa Juridica'),
    ]

    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='pf')

    # Pessoa Fisica
    cpf = models.CharField(max_length=14, blank=True, null=True)

    # Pessoa Juridica
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    razao_social = models.CharField(max_length=200, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True)

    # Contato
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Endereco
    cep = models.CharField(max_length=9, blank=True, null=True)
    logradouro = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organizacao'
        verbose_name_plural = 'Organizacoes'

    def __str__(self):
        return self.nome


class OrganizationMember(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('member', 'Membro'),
    ]

    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('invited', 'Convidado'),
        ('inactive', 'Inativo'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Membro'
        verbose_name_plural = 'Membros'
        unique_together = ['organization', 'user']

    def __str__(self):
        return f'{self.user.email} — {self.organization.nome}'


class Invite(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invites'
    )
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    role = models.CharField(max_length=10, default='member')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invites'
    )
    expires_at = models.DateTimeField()
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Convite'
        verbose_name_plural = 'Convites'

    def __str__(self):
        return f'Convite para {self.email} — {self.organization.nome}'

    def is_valid(self):
        from django.utils import timezone
        return not self.accepted and self.expires_at > timezone.now()