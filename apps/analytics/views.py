from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.campaigns.models import Campaign
from .models import CampaignLog


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