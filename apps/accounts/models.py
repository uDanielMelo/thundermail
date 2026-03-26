from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'cpf']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.email

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Resend
    resend_api_key = models.CharField(max_length=255, blank=True, null=True)
    resend_from_email = models.EmailField(blank=True, null=True)
    
    # Twilio
    twilio_account_sid = models.CharField(max_length=255, blank=True, null=True)
    twilio_auth_token = models.CharField(max_length=255, blank=True, null=True)
    twilio_phone_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Configuracao'
        verbose_name_plural = 'Configuracoes'

    def __str__(self):
        return f'Configuracoes de {self.user.email}'        