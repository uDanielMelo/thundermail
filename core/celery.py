import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'verificar-campanhas-agendadas': {
        'task': 'apps.campaigns.tasks.send_scheduled_campaigns',
        'schedule': 60.0,
    },
    'notificar-tarefas-vencendo': {
        'task': 'apps.tasks.tasks.notify_due_tasks',
        'schedule': crontab(hour=8, minute=0),
    },
}