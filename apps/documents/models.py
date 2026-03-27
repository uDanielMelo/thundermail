import os
from django.db import models
from django.conf import settings


class Folder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    color = models.CharField(max_length=7, default='#6b7280')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name', 'parent')
        verbose_name = 'Pasta'
        verbose_name_plural = 'Pastas'

    def __str__(self):
        return self.name


class Tag(models.Model):
    COLORS = [
        ('gray', 'Cinza'),
        ('red', 'Vermelho'),
        ('orange', 'Laranja'),
        ('yellow', 'Amarelo'),
        ('green', 'Verde'),
        ('blue', 'Azul'),
        ('purple', 'Roxo'),
        ('pink', 'Rosa'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=10, choices=COLORS, default='gray')

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name')
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class Document(models.Model):
    TYPE_CHOICES = [
        ('file', 'Arquivo'),
        ('note', 'Nota'),
        ('link', 'Link'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    tags = models.ManyToManyField(Tag, blank=True, related_name='documents')

    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='file')
    description = models.TextField(blank=True, null=True)

    # Para arquivos
    file = models.FileField(upload_to='documents/%Y/%m/', null=True, blank=True)

    # Para notas
    content = models.TextField(blank=True, null=True)

    # Para links
    url = models.URLField(blank=True, null=True)

    # Metadados
    is_favorite = models.BooleanField(default=False)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return self.title

    def get_file_size_display(self):
        if not self.file_size:
            return ''
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        else:
            return f'{self.file_size / (1024 * 1024):.1f} MB'

    def get_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''

    def is_image(self):
        return self.get_extension() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    def is_pdf(self):
        return self.get_extension() == '.pdf'