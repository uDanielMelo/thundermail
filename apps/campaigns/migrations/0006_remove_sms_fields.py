from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0005_emailtemplate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='channel',
        ),
        migrations.RemoveField(
            model_name='campaign',
            name='sms_message',
        ),
    ]
