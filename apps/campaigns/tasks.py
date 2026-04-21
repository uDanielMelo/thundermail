# apps/campaigns/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import F
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_scheduled_campaigns():
    from .models import Campaign

    now = timezone.now()

    # Recupera campanhas travadas em "enviando" há mais de 30 minutos
    stale_threshold = now - timezone.timedelta(minutes=30)
    stale = Campaign.objects.filter(status='enviando', updated_at__lte=stale_threshold)
    for campaign in stale:
        logger.warning(f"[Campanha {campaign.pk}] travada em 'enviando' — reprocessando")
        campaign.status = 'agendada'
        campaign.total_sent = 0
        campaign.total_failed = 0
        campaign.save(update_fields=['status', 'total_sent', 'total_failed', 'updated_at'])

    # Processa campanhas agendadas
    campaigns = Campaign.objects.filter(status='agendada', scheduled_at__lte=now)

    for campaign in campaigns:
        if not campaign.group:
            campaign.status = 'erro'
            campaign.save(update_fields=['status'])
            continue

        campaign.status = 'enviando'
        campaign.total_sent = 0
        campaign.total_failed = 0
        campaign.save(update_fields=['status', 'total_sent', 'total_failed'])

        send_campaign_in_batches.delay(campaign.pk, offset=0, batch_size=30)


@shared_task
def send_campaign_in_batches(campaign_id, offset=0, batch_size=30):
    from .models import Campaign
    from apps.mailer.services import send_campaign_email
    from apps.analytics.models import CampaignLog
    from apps.contacts.models import Contact

    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"[Campanha {campaign_id}] não encontrada")
        return

    if campaign.status != 'enviando':
        logger.info(f"[Campanha {campaign_id}] status '{campaign.status}' — abortando lote")
        return

    # Resolve o remetente UMA VEZ aqui, antes de iterar
    from_email = _resolve_from_email(campaign.user)
    if not from_email:
        logger.error(f"[Campanha {campaign_id}] sem remetente configurado para user {campaign.user_id}")
        campaign.status = 'erro'
        campaign.save(update_fields=['status'])
        return

    contacts = list(
        Contact.objects.filter(groups=campaign.group, is_unsubscribed=False)
        .exclude(email__isnull=True).exclude(email='')
        .order_by('id')[offset:offset + batch_size]
    )

    sent_in_batch = 0
    failed_in_batch = 0

    for contact in contacts:
        result = send_campaign_email(
            to=[contact.email],
            subject=campaign.subject,
            body=campaign.body,
            from_email=from_email,
            reply_to=campaign.reply_to or None,
            unsubscribe_url=contact.get_unsubscribe_url() if hasattr(contact, 'get_unsubscribe_url') else None,
        )
        if result['success']:
            sent_in_batch += 1
            CampaignLog.objects.create(campaign=campaign, email=contact.email, status='sent')
        else:
            failed_in_batch += 1
            logger.error(f"[Campanha {campaign_id}] falha ao enviar para {contact.email}: {result.get('error')}")
            CampaignLog.objects.create(
                campaign=campaign,
                email=contact.email,
                status='failed',
                error_message=result.get('error', ''),
            )

    # F() evita race condition entre lotes paralelos
    Campaign.objects.filter(pk=campaign_id).update(
        total_sent=F('total_sent') + sent_in_batch,
        total_failed=F('total_failed') + failed_in_batch,
    )

    total_contacts = Contact.objects.filter(
        groups=campaign.group, is_unsubscribed=False
    ).exclude(email__isnull=True).exclude(email='').count()

    next_offset = offset + batch_size

    if next_offset < total_contacts:
        send_campaign_in_batches.apply_async(
            args=[campaign_id, next_offset, batch_size],
            countdown=5,
        )
    else:
        # Último lote — recarrega contadores finais do banco
        campaign.refresh_from_db()
        campaign.status = 'concluida' if campaign.total_failed == 0 else 'erro'
        campaign.sent_at = timezone.now()
        campaign.save(update_fields=['status', 'sent_at'])
        logger.info(
            f"[Campanha {campaign_id}] concluída — "
            f"enviados: {campaign.total_sent}, falhas: {campaign.total_failed}"
        )


def _resolve_from_email(user) -> str | None:
    """
    Retorna o remetente formatado: "Nome Empresa <email@dominio.com>"
    Prioridade: UserSettings > email do usuário
    """
    try:
        from apps.accounts.models import UserSettings
        s = UserSettings.objects.get(user=user)
        if s.resend_from_email:
            if s.nome_remetente:
                return f"{s.nome_remetente} <{s.resend_from_email}>"
            return s.resend_from_email
    except UserSettings.DoesNotExist:
        pass

    # Fallback: email do usuário sem nome estilizado
    if user and user.email:
        nome = user.first_name or user.email.split('@')[0]
        return f"{nome} <{user.email}>"

    return None