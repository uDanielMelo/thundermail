from django.db import models
from apps.campaigns.models import Campaign


class CampaignLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Enviado'),
        ('delivered', 'Entregue'),
        ('opened', 'Aberto'),
        ('clicked', 'Clicado'),
        ('bounced', 'Bounce'),
        ('failed', 'Falhou'),
    ]
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    resend_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de Campanha'
        verbose_name_plural = 'Logs de Campanha'

    def __str__(self):
        return f"{self.campaign.name} - {self.email} - {self.status}"