from django.db import models
from django.conf import settings
from apps.accounts.models import Organization


class Billing(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('RECEIVED', 'Pago'),
        ('CONFIRMED', 'Confirmado'),
        ('OVERDUE', 'Vencido'),
        ('REFUNDED', 'Estornado'),
        ('CANCELLED', 'Cancelado'),
    ]

    PAYMENT_CHOICES = [
        ('PIX', 'Pix'),
        ('BOLETO', 'Boleto'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
    ]

    NOTIFY_CHOICES = [
        ('none', 'Não notificar'),
        ('email', 'E-mail'),
        ('sms', 'SMS'),
        ('both', 'E-mail e SMS'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='billings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Dados do cliente
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_cpf_cnpj = models.CharField(max_length=20, blank=True, null=True)

    # Cobrança
    description = models.CharField(max_length=500)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='PIX')
    notify_via = models.CharField(max_length=10, choices=NOTIFY_CHOICES, default='email')

    # Asaas
    asaas_id = models.CharField(max_length=100, blank=True, null=True)
    asaas_url = models.URLField(blank=True, null=True)
    pix_qrcode = models.TextField(blank=True, null=True)
    pix_payload = models.TextField(blank=True, null=True)
    boleto_url = models.URLField(blank=True, null=True)
    boleto_code = models.TextField(blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cobrança'
        verbose_name_plural = 'Cobranças'

    def __str__(self):
        return f'{self.customer_name} — R$ {self.value}'

    @property
    def status_display_color(self):
        colors = {
            'PENDING': 'yellow',
            'RECEIVED': 'green',
            'CONFIRMED': 'green',
            'OVERDUE': 'red',
            'REFUNDED': 'gray',
            'CANCELLED': 'gray',
        }
        return colors.get(self.status, 'gray')