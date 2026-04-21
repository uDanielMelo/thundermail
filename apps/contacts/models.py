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
    name = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [['organization', 'name']]
        verbose_name = 'Grupo de Contatos'
        verbose_name_plural = 'Grupos de Contatos'

    def __str__(self):
        return self.name


class Contact(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    email = models.EmailField(max_length=512, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    # ManyToMany — um contato pode pertencer a vários grupos
    groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        related_name='contacts'
    )

    unsubscribe_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_unsubscribed = models.BooleanField(default=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email']
        unique_together = [
            ['organization', 'email'],
        ]
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'

    def __str__(self):
        return self.email or str(self.pk)

    def get_unsubscribe_url(self, request=None):
        from django.urls import reverse
        path = reverse('contacts:unsubscribe', kwargs={'token': self.unsubscribe_token})
        if request:
            return request.build_absolute_uri(path)
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}{path}"