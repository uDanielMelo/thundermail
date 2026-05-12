from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from apps.accounts.middleware import get_user_organization
from .models import Campaign
import json


@login_required
def schedule_list(request):
    org = get_user_organization(request.user)

    scheduled = Campaign.objects.filter(
        organization=org,
        status='agendada'
    ).order_by('scheduled_at').select_related('group')

    all_campaigns_with_schedule = Campaign.objects.filter(
        organization=org
    ).exclude(scheduled_at=None).select_related('group')

    events = []
    for c in all_campaigns_with_schedule:
        if c.scheduled_at:
            color = '#1d4ed8' if c.status == 'agendada' else '#16a34a' if c.status == 'concluida' else '#dc2626'
            events.append({
                'id': c.pk,
                'title': c.name,
                'start': timezone.localtime(c.scheduled_at).strftime('%Y-%m-%dT%H:%M:%S'),
                'color': color,
                'status': c.status,
                'group': c.group.name if c.group else 'Sem grupo',
            })

    context = {
        'scheduled': scheduled,
        'events_json': json.dumps(events),
        'all_campaigns': Campaign.objects.filter(
            organization=org,
            status='rascunho'
        ),
    }
    return render(request, 'campaigns/schedule.html', context)


@login_required
def schedule_campaign(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)

    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        if not scheduled_at:
            messages.error(request, 'Informe a data e hora do agendamento.')
            return redirect('schedule:list')

        dt = parse_datetime(scheduled_at)
        if not dt:
            messages.error(request, 'Data inválida.')
            return redirect('schedule:list')

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)

        campaign.scheduled_at = dt
        campaign.status = 'agendada'
        campaign.save()
        messages.success(request, f'Campanha "{campaign.name}" agendada para {dt.strftime("%d/%m/%Y às %H:%M")}!')
        return redirect('schedule:list')

    return redirect('schedule:list')


@login_required
def schedule_cancel(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)
    campaign.scheduled_at = None
    campaign.status = 'rascunho'
    campaign.save()
    messages.success(request, f'Agendamento de "{campaign.name}" cancelado.')
    return redirect('schedule:list')