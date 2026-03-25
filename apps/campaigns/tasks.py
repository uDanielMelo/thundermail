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

        contacts = Contact.objects.filter(group=campaign.group)
        emails = [c.email for c in contacts]

        total_sent = 0
        total_failed = 0

        for email in emails:
            result = send_campaign_email(
                to=[email],
                subject=campaign.subject,
                body=campaign.body,
                reply_to=campaign.reply_to or None
            )
            if result['success']:
                total_sent += 1
                CampaignLog.objects.create(
                    campaign=campaign,
                    email=email,
                    status='sent'
                )
            else:
                total_failed += 1
                CampaignLog.objects.create(
                    campaign=campaign,
                    email=email,
                    status='failed',
                    error_message=result.get('error', '')
                )

        campaign.total_sent = total_sent
        campaign.total_failed = total_failed
        campaign.status = 'concluida' if total_failed == 0 else 'erro'
        campaign.save()