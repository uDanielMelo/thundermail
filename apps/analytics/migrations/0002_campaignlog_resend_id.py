from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignlog',
            name='resend_id',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
