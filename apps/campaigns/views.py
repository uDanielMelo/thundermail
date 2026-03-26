from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Campaign
from apps.contacts.models import ContactGroup, Contact
from apps.mailer.services import send_campaign_email
from apps.analytics.models import CampaignLog


def _send_campaign(campaign, group):
    """Função auxiliar reutilizada no create e no edit."""
    contacts = Contact.objects.filter(group=group, is_unsubscribed=False)

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
    return total_sent, total_failed


@login_required
def campaigns_list(request):
    search = request.GET.get('q', '')
    channel = request.GET.get('channel', 'email')

    campaigns = Campaign.objects.filter(user=request.user, channel=channel)
    if search:
        campaigns = campaigns.filter(name__icontains=search)

    return render(request, 'campaigns/list.html', {
        'campaigns': campaigns,
        'search': search,
        'channel': channel,
    })


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

        campaign = Campaign.objects.create(
            user=request.user,
            name=name,
            subject=subject,
            body=body,
            group=group,
            reply_to=reply_to,
            status='enviando' if action == 'send' else 'rascunho'
        )

        if action == 'send' and group:
            total_sent, total_failed = _send_campaign(campaign, group)
            messages.success(request, f'Campanha enviada! {total_sent} enviados, {total_failed} falhas.')
        else:
            messages.success(request, 'Rascunho salvo com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/create.html', {'groups': groups})


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
            total_sent, total_failed = _send_campaign(campaign, group)
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
def campaign_create_sms(request):
    groups = ContactGroup.objects.filter(user=request.user)

    from apps.accounts.models import UserSettings
    try:
        user_settings = UserSettings.objects.get(user=request.user)
        twilio_configured = bool(user_settings.twilio_account_sid)
    except UserSettings.DoesNotExist:
        twilio_configured = False

    if request.method == 'POST':
        name = request.POST.get('name')
        sms_message = request.POST.get('sms_message')
        group_id = request.POST.get('group')
        action = request.POST.get('action')

        if not name or not sms_message:
            messages.error(request, 'Preencha todos os campos obrigatorios.')
            return render(request, 'campaigns/create_sms.html', {
                'groups': groups,
                'twilio_configured': twilio_configured
            })

        group = None
        if group_id:
            group = get_object_or_404(ContactGroup, pk=group_id, user=request.user)

        campaign = Campaign.objects.create(
            user=request.user,
            name=name,
            sms_message=sms_message,
            group=group,
            channel='sms',
            status='rascunho'
        )

        if action == 'send' and group and twilio_configured:
            from apps.mailer.sms_services import send_sms
            sms_contacts = Contact.objects.filter(
                group=group
            ).exclude(phone__isnull=True).exclude(phone='')

            total_sent = 0
            total_failed = 0

            for contact in sms_contacts:
                result = send_sms(
                    to=contact.phone,
                    message=sms_message,
                    user=request.user
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
            messages.success(request, f'SMS enviado! {total_sent} enviados, {total_failed} falhas.')
        else:
            messages.success(request, 'Rascunho SMS salvo com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/create_sms.html', {
        'groups': groups,
        'twilio_configured': twilio_configured
    })