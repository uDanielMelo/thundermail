from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_campaignlog_resend_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaignlog',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('sent', 'Enviado'),
                    ('delivered', 'Entregue'),
                    ('opened', 'Aberto'),
                    ('clicked', 'Clicado'),
                    ('bounced', 'Bounce'),
                    ('failed', 'Falhou'),
                ],
            ),
        ),
    ]