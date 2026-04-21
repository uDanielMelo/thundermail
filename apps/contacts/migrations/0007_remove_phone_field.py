from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0006_contact_groups_m2m'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together={('organization', 'email')},
        ),
        migrations.RemoveField(
            model_name='contact',
            name='phone',
        ),
    ]
