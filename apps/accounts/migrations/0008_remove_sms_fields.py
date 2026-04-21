from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_memberpermission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersettings',
            name='twilio_account_sid',
        ),
        migrations.RemoveField(
            model_name='usersettings',
            name='twilio_auth_token',
        ),
        migrations.RemoveField(
            model_name='usersettings',
            name='twilio_phone_number',
        ),
        migrations.RemoveField(
            model_name='memberpermission',
            name='sms_marketing',
        ),
    ]
