from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Campaign
import json


@login_required
def schedule_list(request):
    scheduled = Campaign.objects.filter(
        user=request.user,
        status='agendada'
    ).order_by('scheduled_at')

    all_campaigns = Campaign.objects.filter(
        user=request.user
    ).exclude(scheduled_at=None).order_by('scheduled_at')

    # Monta eventos para o calendário
    events = []
    for c in all_campaigns:
        if c.scheduled_at:
            color = '#1d4ed8' if c.status == 'agendada' else '#16a34a' if c.status == 'concluida' else '#dc2626'
            events.append({
                'id': c.pk,
                'title': c.name,
                'start': c.scheduled_at.strftime('%Y-%m-%dT%H:%M:%S'),
                'color': color,
                'status': c.status,
            })

    context = {
        'scheduled': scheduled,
        'events_json': json.dumps(events),
        'all_campaigns': Campaign.objects.filter(
            user=request.user,
            status='rascunho'
        ),
    }
    return render(request, 'campaigns/schedule.html', context)


@login_required
def schedule_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)

    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        if not scheduled_at:
            messages.error(request, 'Informe a data e hora do agendamento.')
            return redirect('schedule:list')

        from django.utils.dateparse import parse_datetime
        dt = parse_datetime(scheduled_at)
        if not dt:
            messages.error(request, 'Data inválida.')
            return redirect('schedule:list')

        campaign.scheduled_at = dt
        campaign.status = 'agendada'
        campaign.save()
        messages.success(request, f'Campanha "{campaign.name}" agendada com sucesso!')
        return redirect('schedule:list')

    return redirect('schedule:list')


@login_required
def schedule_cancel(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    campaign.scheduled_at = None
    campaign.status = 'rascunho'
    campaign.save()
    messages.success(request, f'Agendamento de "{campaign.name}" cancelado.')
    return redirect('schedule:list')