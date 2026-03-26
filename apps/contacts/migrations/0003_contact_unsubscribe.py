from django.db import migrations, models
import uuid


def populate_tokens(apps, schema_editor):
    Contact = apps.get_model('contacts', 'Contact')
    for contact in Contact.objects.all():
        contact.unsubscribe_token = uuid.uuid4()
        contact.save(update_fields=['unsubscribe_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_contact_phone'),
    ]

    operations = [
        # 1. Adiciona o campo SEM unique, com um default fixo temporário
        migrations.AddField(
            model_name='contact',
            name='unsubscribe_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        # 2. Popula cada contato existente com um UUID único
        migrations.RunPython(populate_tokens, migrations.RunPython.noop),
        # 3. Agora sim adiciona o índice único
        migrations.AlterField(
            model_name='contact',
            name='unsubscribe_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        # 4. Campos restantes
        migrations.AddField(
            model_name='contact',
            name='is_unsubscribed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contact',
            name='unsubscribed_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]