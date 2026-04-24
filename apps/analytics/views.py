import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import CampaignLog

logger = logging.getLogger(__name__)

RESEND_EVENT_MAP = {
    'email.delivered': 'delivered',
    'email.opened':    'opened',
    'email.clicked':   'clicked',
    'email.bounced':   'bounced',
}


@csrf_exempt
@require_POST
def resend_webhook(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)

    event_type = payload.get('type', '')
    data       = payload.get('data', {})
    resend_id  = data.get('email_id') or data.get('id', '')

    new_status = RESEND_EVENT_MAP.get(event_type)
    if not new_status:
        # Evento que não rastreamos — responde 200 para o Resend não retentar
        return JsonResponse({'ignored': True})

    if not resend_id:
        logger.warning('Webhook Resend sem email_id: %s', payload)
        return JsonResponse({'error': 'no email_id'}, status=400)

    updated = CampaignLog.objects.filter(resend_id=resend_id).update(status=new_status)

    if updated == 0:
        logger.warning('Webhook Resend: resend_id não encontrado: %s', resend_id)

    logger.info('Webhook Resend: %s → %s (%d log(s) atualizados)', resend_id, new_status, updated)
    return JsonResponse({'ok': True, 'updated': updated})