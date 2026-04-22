import hmac
import hashlib
import json
import logging
import time

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings

from apps.campaigns.models import Campaign
from .models import CampaignLog

logger = logging.getLogger(__name__)

# Eventos do Resend que mapeiam para status no CampaignLog
RESEND_EVENT_MAP = {
    'email.opened': 'opened',
    'email.clicked': 'clicked',
    'email.bounced': 'failed',
    'email.complained': 'failed',
}


def _verify_resend_signature(request) -> bool:
    """Verifica assinatura Svix enviada pelo Resend."""
    secret = getattr(settings, 'RESEND_WEBHOOK_SECRET', '')
    if not secret:
        logger.warning('[Resend Webhook] RESEND_WEBHOOK_SECRET não configurado — pulando verificação')
        return True

    svix_id = request.headers.get('svix-id', '')
    svix_timestamp = request.headers.get('svix-timestamp', '')
    svix_signature = request.headers.get('svix-signature', '')

    if not (svix_id and svix_timestamp and svix_signature):
        return False

    # Rejeita payloads com timestamp fora de 5 minutos
    try:
        ts = int(svix_timestamp)
        if abs(time.time() - ts) > 300:
            return False
    except (ValueError, TypeError):
        return False

    # Monta a mensagem e verifica o HMAC-SHA256
    signed_content = f'{svix_id}.{svix_timestamp}.{request.body.decode("utf-8")}'
    # Secret começa com "whsec_" — remove prefixo e decodifica base64
    import base64
    raw_secret = base64.b64decode(secret.removeprefix('whsec_'))
    expected = hmac.new(raw_secret, signed_content.encode(), hashlib.sha256).digest()
    expected_b64 = base64.b64encode(expected).decode()

    # svix-signature pode ter múltiplos valores separados por espaço
    for sig in svix_signature.split(' '):
        if sig.startswith('v1,') and hmac.compare_digest(sig[3:], expected_b64):
            return True

    return False


@csrf_exempt
@require_POST
def resend_webhook(request):
    if not _verify_resend_signature(request):
        logger.warning('[Resend Webhook] assinatura inválida')
        return HttpResponseForbidden('Invalid signature')

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse('Bad payload', status=400)

    event_type = payload.get('type', '')
    data = payload.get('data', {})
    resend_email_id = data.get('email_id') or data.get('id', '')

    logger.info(f'[Resend Webhook] evento={event_type} resend_id={resend_email_id}')

    if not resend_email_id:
        return HttpResponse('OK')

    new_status = RESEND_EVENT_MAP.get(event_type)
    if not new_status:
        return HttpResponse('OK')

    log = CampaignLog.objects.filter(resend_id=resend_email_id).first()
    if not log:
        logger.warning(f'[Resend Webhook] CampaignLog não encontrado para resend_id={resend_email_id}')
        return HttpResponse('OK')

    # Para opened/clicked: cria novo registro (permite múltiplos eventos)
    # Para bounced/complained: atualiza o log existente
    if new_status in ('opened', 'clicked'):
        already = CampaignLog.objects.filter(
            campaign=log.campaign,
            email=log.email,
            status=new_status,
        ).exists()
        if not already:
            CampaignLog.objects.create(
                campaign=log.campaign,
                email=log.email,
                status=new_status,
                resend_id=resend_email_id,
            )
            logger.info(f'[Resend Webhook] {new_status} registrado — campanha={log.campaign_id} email={log.email}')
    else:
        log.status = new_status
        log.error_message = f'Evento Resend: {event_type}'
        log.save(update_fields=['status', 'error_message'])
        logger.info(f'[Resend Webhook] {new_status} atualizado — campanha={log.campaign_id} email={log.email}')

    return HttpResponse('OK')


@login_required
def campaign_analytics(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    logs = CampaignLog.objects.filter(campaign=campaign)

    total_sent = logs.filter(status='sent').count()
    total_failed = logs.filter(status='failed').count()
    total = logs.count()

    success_rate = round((total_sent / total * 100), 1) if total > 0 else 0

    context = {
        'campaign': campaign,
        'logs': logs,
        'total_sent': total_sent,
        'total_failed': total_failed,
        'total': total,
        'success_rate': success_rate,
    }
    return render(request, 'analytics/campaign.html', context)