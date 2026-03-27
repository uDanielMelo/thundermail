from django.db import models
from django.conf import settings


class Integration(models.Model):
    PLATFORM_CHOICES = [
        ('google_analytics', 'Google Analytics'),
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='integrations')
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'platform')
        verbose_name = 'Integração'
        verbose_name_plural = 'Integrações'

    def __str__(self):
        return f'{self.user.email} — {self.get_platform_display()}'