from django.db import models
from django.conf import settings
from apps.contacts.models import ContactGroup


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('agendada', 'Agendada'),
        ('enviando', 'Enviando'),
        ('concluida', 'Concluida'),
        ('erro', 'Erro'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'E-mail'),
        ('sms', 'SMS'),
        ('both', 'E-mail e SMS'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=300, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    group = models.ForeignKey(
        ContactGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns'
    )
    reply_to = models.EmailField(blank=True, null=True)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    sms_message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_sent = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'

    def __str__(self):
        return self.name