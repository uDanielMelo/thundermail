from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Campaign
from apps.contacts.models import ContactGroup


@login_required
def campaigns_list(request):
    campaigns = Campaign.objects.filter(user=request.user)
    return render(request, 'campaigns/list.html', {'campaigns': campaigns})


@login_required
def campaign_create(request):
    groups = ContactGroup.objects.filter(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        group_id = request.POST.get('group')
        action = request.POST.get('action')

        if not name or not subject or not body:
            messages.error(request, 'Nome, assunto e corpo são obrigatórios.')
            return render(request, 'campaigns/create.html', {'groups': groups})

        group = None
        if group_id:
            group = get_object_or_404(ContactGroup, pk=group_id, user=request.user)

        status = 'rascunho'
        if action == 'send':
            status = 'enviando'

        campaign = Campaign.objects.create(
            user=request.user,
            name=name,
            subject=subject,
            body=body,
            group=group,
            status=status
        )

        if action == 'send' and group:
            from apps.mailer.services import send_campaign_email
            from apps.contacts.models import Contact
            from apps.analytics.models import CampaignLog

            contacts = Contact.objects.filter(group=group)
            emails = [c.email for c in contacts]

            total_sent = 0
            total_failed = 0

            for email in emails:
                result = send_campaign_email(
                    to=[email],
                    subject=subject,
                    body=body
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

            messages.success(request, f'Campanha enviada! {total_sent} enviados, {total_failed} falhas.')
        else:
            messages.success(request, f'Rascunho "{name}" salvo com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/create.html', {'groups': groups})


@login_required
def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    return render(request, 'campaigns/detail.html', {'campaign': campaign})


@login_required
def campaign_delete(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    campaign.delete()
    messages.success(request, 'Campanha deletada com sucesso.')
    return redirect('campaigns:list')