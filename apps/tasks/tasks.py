from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def notify_due_tasks():
    from .models import Task
    from apps.mailer.services import send_campaign_email

    tomorrow = timezone.now().date() + timedelta(days=1)
    tasks = Task.objects.filter(
        due_date=tomorrow,
        status__in=['todo', 'doing'],
        assigned_to__isnull=False,
    ).select_related('assigned_to', 'project', 'created_by')

    for task in tasks:
        try:
            send_campaign_email(
                to=[task.assigned_to.email],
                subject=f'⏰ Tarefa vence amanhã: {task.title}',
                body=f'''
                    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
                        <h2 style="color:#111;">Sua tarefa vence amanhã!</h2>
                        <div style="background:#fffbeb;border-left:4px solid #f59e0b;padding:12px 16px;margin:16px 0;border-radius:4px;">
                            <p style="font-size:16px;font-weight:500;margin:0;">{task.title}</p>
                            <p style="color:#666;margin:4px 0 0;">Projeto: {task.project.name}</p>
                        </div>
                        <p style="color:#666;font-size:14px;">Não esqueça de concluir ou atualizar o status desta tarefa!</p>
                    </div>
                ''',
                user=task.created_by,
            )
        except Exception as e:
            print(f'Erro ao notificar prazo: {e}')