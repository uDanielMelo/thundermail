from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Campaign
from apps.contacts.models import ContactGroup
from apps.mailer.services import send_campaign_email
from apps.analytics.models import CampaignLog
from apps.contacts.models import Contact


@login_required
def campaigns_list(request):
    search = request.GET.get('q', '')
    campaigns = Campaign.objects.filter(user=request.user)
    if search:
        campaigns = campaigns.filter(name__icontains=search)
    return render(request, 'campaigns/list.html', {
        'campaigns': campaigns,
        'search': search
    })


@login_required
def campaign_edit(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    groups = ContactGroup.objects.filter(user=request.user)

    if campaign.status != 'rascunho':
        messages.error(request, 'Apenas rascunhos podem ser editados.')
        return redirect('campaigns:list')

    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        group_id = request.POST.get('group')
        action = request.POST.get('action')
        reply_to = request.POST.get('reply_to', '')

        if not name or not subject or not body:
            messages.error(request, 'Preencha todos os campos obrigatorios.')
            return render(request, 'campaigns/edit.html', {'campaign': campaign, 'groups': groups})

        group = None
        if group_id:
            group = get_object_or_404(ContactGroup, pk=group_id, user=request.user)

        campaign.name = name
        campaign.subject = subject
        campaign.body = body
        campaign.group = group
        campaign.reply_to = reply_to

        if action == 'send' and group:
            campaign.status = 'enviando'
            campaign.save()

            contacts = Contact.objects.filter(group=group)
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
            messages.success(request, f'Campanha enviada! {total_sent} enviados, {total_failed} falhas.')
        else:
            campaign.status = 'rascunho'
            campaign.save()
            messages.success(request, 'Rascunho atualizado com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/edit.html', {'campaign': campaign, 'groups': groups})

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

@login_required
def campaign_duplicate(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    Campaign.objects.create(
        user=request.user,
        name=f'{campaign.name} (cópia)',
        subject=campaign.subject,
        body=campaign.body,
        group=campaign.group,
        reply_to=campaign.reply_to,
        status='rascunho'
    )
    messages.success(request, f'Campanha "{campaign.name}" duplicada com sucesso!')
    return redirect('campaigns:list')

@login_required
def campaign_create(request):
    groups = ContactGroup.objects.filter(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        group_id = request.POST.get('group')
        action = request.POST.get('action')
        reply_to = request.POST.get('reply_to', '')

        if not name or not subject or not body:
            messages.error(request, 'Preencha todos os campos obrigatorios.')
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
            reply_to=reply_to,
            status=status
        )

        if action == 'send' and group:
            contacts = Contact.objects.filter(group=group)
            emails = [c.email for c in contacts]

            total_sent = 0
            total_failed = 0

            for email in emails:
                result = send_campaign_email(
                    to=[email],
                    subject=subject,
                    body=body,
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
            messages.success(request, f'Campanha enviada! {total_sent} enviados, {total_failed} falhas.')
        else:
            messages.success(request, f'Rascunho salvo com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/create.html', {'groups': groups})