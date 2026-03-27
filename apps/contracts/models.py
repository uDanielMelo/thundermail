import uuid
from django.db import models
from django.conf import settings


class Contract(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado'),
        ('parcial', 'Parcialmente assinado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contracts')
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='contracts/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    message = models.TextField(blank=True, null=True, help_text='Mensagem enviada por e-mail aos signatários')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'

    def __str__(self):
        return self.title

    def total_signers(self):
        return self.signers.count()

    def signed_count(self):
        return self.signers.filter(status='assinado').count()

    def is_complete(self):
        return self.total_signers() > 0 and self.signed_count() == self.total_signers()


class ContractSigner(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('visualizado', 'Visualizado'),
        ('assinado', 'Assinado'),
        ('recusado', 'Recusado'),
    ]

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='signers')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    cpf = models.CharField(max_length=14, blank=True, null=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    # Dados da assinatura
    signed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    # Assinatura desenhada (base64)
    signature_data = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Signatário'
        verbose_name_plural = 'Signatários'

    def __str__(self):
        return f'{self.name} — {self.contract.title}'

    def get_sign_url(self):
        from django.urls import reverse
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        path = reverse('contracts:sign', kwargs={'token': self.token})
        return f"{base_url}{path}"