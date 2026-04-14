# apps/campaigns/tasks.py
from celery import shared_task
from django.utils import timezone


@shared_task
def send_scheduled_campaigns():
    from .models import Campaign
    from apps.mailer.services import send_campaign_email
    from apps.analytics.models import CampaignLog
    from apps.contacts.models import Contact

    now = timezone.now()
    campaigns = Campaign.objects.filter(status='agendada', scheduled_at__lte=now)

    for campaign in campaigns:
        if not campaign.group:
            campaign.status = 'erro'
            campaign.save()
            continue

        contacts = list(Contact.objects.filter(groups=campaign.group, is_unsubscribed=False))

        total_sent = 0
        total_failed = 0

        for contact in contacts:
            result = send_campaign_email(
                to=[contact.email],
                subject=campaign.subject,
                body=campaign.body,
                reply_to=campaign.reply_to or None,
                unsubscribe_url=contact.get_unsubscribe_url() if hasattr(contact, 'get_unsubscribe_url') else None,
                user=campaign.user,
            )
            if result['success']:
                total_sent += 1
                CampaignLog.objects.create(campaign=campaign, email=contact.email, status='sent')
            else:
                total_failed += 1
                CampaignLog.objects.create(campaign=campaign, email=contact.email, status='failed',
                                           error_message=result.get('error', ''))

        campaign.total_sent = total_sent
        campaign.total_failed = total_failed
        campaign.status = 'concluida' if total_failed == 0 else 'erro'
        campaign.save()


@shared_task
def send_campaign_in_batches(campaign_id, offset=0, batch_size=30):
    from .models import Campaign
    from apps.mailer.services import send_campaign_email
    from apps.analytics.models import CampaignLog
    from apps.contacts.models import Contact

    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        return

    if campaign.status != 'enviando':
        return

    contacts = list(
        Contact.objects.filter(groups=campaign.group, is_unsubscribed=False)
        .order_by('id')[offset:offset + batch_size]
    )

    total_sent = campaign.total_sent or 0
    total_failed = campaign.total_failed or 0

    for contact in contacts:
        result = send_campaign_email(
            to=[contact.email],
            subject=campaign.subject,
            body=campaign.body,
            reply_to=campaign.reply_to or None,
            unsubscribe_url=contact.get_unsubscribe_url() if hasattr(contact, 'get_unsubscribe_url') else None,
            user=campaign.user,
        )
        if result['success']:
            total_sent += 1
            CampaignLog.objects.create(campaign=campaign, email=contact.email, status='sent')
        else:
            total_failed += 1
            CampaignLog.objects.create(campaign=campaign, email=contact.email, status='failed',
                                       error_message=result.get('error', ''))

    campaign.total_sent = total_sent
    campaign.total_failed = total_failed
    campaign.save(update_fields=['total_sent', 'total_failed'])

    total_contacts = Contact.objects.filter(groups=campaign.group, is_unsubscribed=False).count()
    next_offset = offset + batch_size

    if next_offset < total_contacts:
        send_campaign_in_batches.apply_async(
            args=[campaign_id, next_offset, batch_size],
            countdown=5
        )
    else:
        campaign.status = 'concluida' if total_failed == 0 else 'erro'
        campaign.save(update_fields=['status'])