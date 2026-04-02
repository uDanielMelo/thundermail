import uuid
from django.db import models
from django.conf import settings
from apps.accounts.models import Organization


class ContactGroup(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contact_groups',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Grupo de Contatos'
        verbose_name_plural = 'Grupos de Contatos'

    def __str__(self):
        return self.name

    @property
    def total_contacts(self):
        return self.contacts.count()


class Contact(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    email = models.EmailField(max_length=512)
    phone = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    group = models.ForeignKey(
        ContactGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts'
    )

    # Unsubscribe
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_unsubscribed = models.BooleanField(default=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email']
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'

    def __str__(self):
        return self.email

    def get_unsubscribe_url(self, request=None):
        from django.urls import reverse
        path = reverse('contacts:unsubscribe', kwargs={'token': self.unsubscribe_token})
        if request:
            return request.build_absolute_uri(path)
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}{path}"