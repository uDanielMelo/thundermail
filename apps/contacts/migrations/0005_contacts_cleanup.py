import django.db.models.deletion
from django.db import migrations, models


def remove_sms_local_contacts(apps, schema_editor):
    Contact = apps.get_model('contacts', 'Contact')

    for contact in Contact.objects.filter(email__endswith='@sms.local'):
        phone = contact.phone
        if not phone:
            phone = contact.email.replace('@sms.local', '')

        real = Contact.objects.filter(
            organization=contact.organization,
            phone=phone,
        ).exclude(email__endswith='@sms.local').first()

        if real:
            contact.delete()
        else:
            contact.email = None
            contact.save(update_fields=['email'])


def normalize_empty_strings(apps, schema_editor):
    """
    Converte phone='' e email='' para NULL.
    PostgreSQL trata '' como valor concreto — dois registros com phone=''
    na mesma organização violam o unique_together. NULL é ignorado pelo índice.
    """
    Contact = apps.get_model('contacts', 'Contact')
    Contact.objects.filter(phone='').update(phone=None)
    Contact.objects.filter(email='').update(email=None)


def remove_duplicate_emails(apps, schema_editor):
    Contact = apps.get_model('contacts', 'Contact')

    seen = {}
    for contact in Contact.objects.filter(email__isnull=False).order_by('pk'):
        key = (contact.organization_id, contact.email.lower())
        if key in seen:
            contact.delete()
        else:
            seen[key] = contact.pk


def remove_duplicate_phones(apps, schema_editor):
    Contact = apps.get_model('contacts', 'Contact')

    seen = {}
    for contact in Contact.objects.filter(phone__isnull=False).order_by('pk'):
        key = (contact.organization_id, contact.phone)
        if key in seen:
            contact.delete()
        else:
            seen[key] = contact.pk


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0004_alter_contact_unique_together_and_more'),
    ]

    operations = [
        # 1. Limpa contatos @sms.local
        migrations.RunPython(remove_sms_local_contacts, migrations.RunPython.noop),

        # 2. Normaliza strings vazias para NULL antes de qualquer índice único
        migrations.RunPython(normalize_empty_strings, migrations.RunPython.noop),

        # 3. Remove duplicatas
        migrations.RunPython(remove_duplicate_emails, migrations.RunPython.noop),
        migrations.RunPython(remove_duplicate_phones, migrations.RunPython.noop),

        # 4. Remove campo user de ContactGroup
        migrations.RemoveField(
            model_name='contactgroup',
            name='user',
        ),

        # 5. Remove campo user de Contact
        migrations.RemoveField(
            model_name='contact',
            name='user',
        ),

        # 6. Torna email nullable
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(blank=True, max_length=512, null=True),
        ),

        # 7. unique_together em ContactGroup
        migrations.AlterUniqueTogether(
            name='contactgroup',
            unique_together={('organization', 'name')},
        ),

        # 8. unique_together em Contact
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together={('organization', 'email'), ('organization', 'phone')},
        ),
    ]