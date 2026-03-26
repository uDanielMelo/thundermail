from celery import shared_task
from django.utils import timezone


@shared_task
def send_scheduled_campaigns():
    from .models import Campaign
    from apps.mailer.services import send_campaign_email
    from apps.analytics.models import CampaignLog
    from apps.contacts.models import Contact

    now = timezone.now()
    campaigns = Campaign.objects.filter(
        status='agendada',
        scheduled_at__lte=now
    )

    for campaign in campaigns:
        if not campaign.group:
            campaign.status = 'erro'
            campaign.save()
            continue

        # Ignora contatos descadastrados
        contacts = Contact.objects.filter(
            group=campaign.group,
            is_unsubscribed=False
        )

        total_sent = 0
        total_failed = 0

        for contact in contacts:
            result = send_campaign_email(
                to=[contact.email],
                subject=campaign.subject,
                body=campaign.body,
                reply_to=campaign.reply_to or None,
                unsubscribe_url=contact.get_unsubscribe_url(),
            )
            if result['success']:
                total_sent += 1
                CampaignLog.objects.create(
                    campaign=campaign,
                    email=contact.email,
                    status='sent'
                )
            else:
                total_failed += 1
                CampaignLog.objects.create(
                    campaign=campaign,
                    email=contact.email,
                    status='failed',
                    error_message=result.get('error', '')
                )

        campaign.total_sent = total_sent
        campaign.total_failed = total_failed
        campaign.status = 'concluida' if total_failed == 0 else 'erro'
        campaign.save()