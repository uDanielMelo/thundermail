from django.db import migrations, models


def migrate_fk_to_m2m(apps, schema_editor):
    """
    Migra os dados da FK Contact.group para a tabela M2M Contact.groups.
    Cada contato que tinha group != NULL é adicionado ao novo M2M.
    """
    Contact = apps.get_model('contacts', 'Contact')
    # A tabela M2M ainda não existe como campo no model histórico,
    # então usamos SQL direto para popular a tabela intermediária.
    db_alias = schema_editor.connection.alias
    through_model = Contact.groups.through if hasattr(Contact, 'groups') else None

    # Usamos o schema_editor para executar SQL direto
    schema_editor.execute("""
        INSERT INTO contacts_contact_groups (contact_id, contactgroup_id)
        SELECT id, group_id
        FROM contacts_contact
        WHERE group_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0005_contacts_cleanup'),
    ]

    operations = [
        # 1. Cria a tabela M2M
        migrations.AddField(
            model_name='contact',
            name='groups',
            field=models.ManyToManyField(
                blank=True,
                related_name='contacts',
                to='contacts.contactgroup',
            ),
        ),

        # 2. Migra dados da FK para o M2M
        migrations.RunPython(migrate_fk_to_m2m, migrations.RunPython.noop),

        # 3. Remove a FK antiga (group)
        migrations.RemoveField(
            model_name='contact',
            name='group',
        ),
    ]