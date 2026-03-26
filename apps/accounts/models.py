from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    TIPO_CHOICES = [
        ('pf', 'Pessoa Fisica'),
        ('pj', 'Pessoa Juridica'),
    ]

    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='pf')

    # Pessoa Fisica
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(null=True, blank=True)

    # Pessoa Juridica
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    razao_social = models.CharField(max_length=200, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True)

    # Contato
    telefone = models.CharField(max_length=20, blank=True, null=True)

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.email