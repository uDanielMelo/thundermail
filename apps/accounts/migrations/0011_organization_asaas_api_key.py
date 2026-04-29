from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_remove_usersettings_resend_api_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='asaas_api_key',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
