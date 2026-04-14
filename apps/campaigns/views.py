# apps/campaigns/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Campaign
from apps.contacts.models import ContactGroup, Contact
from apps.mailer.services import send_campaign_email
from apps.analytics.models import CampaignLog
from apps.accounts.middleware import get_user_organization
from apps.accounts.decorators import require_permission
from django.db.models import Count


def _send_campaign(campaign, group):
    contacts = Contact.objects.filter(groups=group, is_unsubscribed=False)

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
@require_permission('email_marketing')
def campaigns_list(request):
    org = get_user_organization(request.user)
    search = request.GET.get('q', '')
    channel = request.GET.get('channel', 'email')

    campaigns = Campaign.objects.filter(organization=org, channel=channel)
    if search:
        campaigns = campaigns.filter(name__icontains=search)

    return render(request, 'campaigns/list.html', {
        'campaigns': campaigns,
        'search': search,
        'channel': channel,
    })


@login_required
@require_permission('email_marketing')
def campaign_create(request):
    org = get_user_organization(request.user)
    groups = ContactGroup.objects.filter(organization=org).annotate(
    total_contacts=Count('contacts')
    )

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
            group = get_object_or_404(ContactGroup, pk=group_id, organization=org)

        campaign = Campaign.objects.create(
            organization=org,
            user=request.user,
            name=name,
            subject=subject,
            body=body,
            group=group,
            reply_to=reply_to,
            status='rascunho'
        )

        if action == 'send' and group:
            campaign.status = 'enviando'
            campaign.total_sent = 0
            campaign.total_failed = 0
            campaign.save()
            from .tasks import send_campaign_in_batches
            send_campaign_in_batches.delay(campaign.pk, offset=0, batch_size=30)
            messages.success(request, 'Campanha em envio! Acompanhe o progresso na lista.')
        else:
            messages.success(request, 'Rascunho salvo com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/create.html', {'groups': groups})


@login_required
@require_permission('email_marketing')
def campaign_edit(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)
    groups = ContactGroup.objects.filter(organization=org).annotate(
    total_contacts=Count('contacts')
    )

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
            group = get_object_or_404(ContactGroup, pk=group_id, organization=org)

        campaign.name = name
        campaign.subject = subject
        campaign.body = body
        campaign.group = group
        campaign.reply_to = reply_to

        if action == 'send' and group:
            campaign.status = 'enviando'
            campaign.total_sent = 0
            campaign.total_failed = 0
            campaign.save()
            from .tasks import send_campaign_in_batches
            send_campaign_in_batches.delay(campaign.pk, offset=0, batch_size=30)
            messages.success(request, 'Campanha em envio! Acompanhe o progresso na lista.')
        else:
            campaign.status = 'rascunho'
            campaign.save()
            messages.success(request, 'Rascunho atualizado com sucesso!')

        return redirect('campaigns:list')

    return render(request, 'campaigns/edit.html', {'campaign': campaign, 'groups': groups})


@login_required
@require_permission('email_marketing')
def campaign_detail(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)
    return render(request, 'campaigns/detail.html', {'campaign': campaign})


@login_required
@require_permission('email_marketing')
def campaign_delete(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)
    campaign.delete()
    messages.success(request, 'Campanha deletada com sucesso.')
    return redirect('campaigns:list')


@login_required
@require_permission('email_marketing')
def campaign_duplicate(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)
    Campaign.objects.create(
        organization=org,
        user=request.user,
        name=f'{campaign.name} (copia)',
        subject=campaign.subject,
        body=campaign.body,
        group=campaign.group,
        reply_to=campaign.reply_to,
        status='rascunho'
    )
    messages.success(request, f'Campanha "{campaign.name}" duplicada com sucesso!')
    return redirect('campaigns:list')


@login_required
@require_permission('email_marketing')
@require_POST
def campaign_send_now(request, pk):
    from .tasks import send_campaign_in_batches
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)

    if campaign.status != 'rascunho':
        return JsonResponse({'error': 'Campanha não pode ser enviada neste estado.'}, status=400)

    if not campaign.group:
        return JsonResponse({'error': 'Campanha sem grupo de contatos.'}, status=400)

    total = Contact.objects.filter(groups=campaign.group, is_unsubscribed=False).count()
    if total == 0:
        return JsonResponse({'error': 'Nenhum contato elegível no grupo.'}, status=400)

    campaign.status = 'enviando'
    campaign.total_sent = 0
    campaign.total_failed = 0
    campaign.save()

    send_campaign_in_batches.delay(campaign.pk, offset=0, batch_size=30)

    return JsonResponse({'ok': True, 'total': total})


@login_required
@require_permission('email_marketing')
def campaign_send_status(request, pk):
    org = get_user_organization(request.user)
    campaign = get_object_or_404(Campaign, pk=pk, organization=org)
    total = Contact.objects.filter(groups=campaign.group, is_unsubscribed=False).count() if campaign.group else 0
    return JsonResponse({
        'status': campaign.status,
        'total_sent': campaign.total_sent or 0,
        'total_failed': campaign.total_failed or 0,
        'total': total,
    })


@login_required
@require_permission('sms_marketing')
def campaign_create_sms(request):
    org = get_user_organization(request.user)
    groups = ContactGroup.objects.filter(organization=org).annotate(
    total_contacts=Count('contacts')
    )

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
            group = get_object_or_404(ContactGroup, pk=group_id, organization=org)

        campaign = Campaign.objects.create(
            organization=org,
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
                groups=group
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

@login_required
@require_permission('email_marketing')
def template_save(request):
    from .models import EmailTemplate
    if request.method == 'POST':
        import json
        org = get_user_organization(request.user)
        name = request.POST.get('name', '').strip()
        body = request.POST.get('body', '')
        design_raw = request.POST.get('design', '')

        if not name or not body:
            return JsonResponse({'error': 'Nome e corpo são obrigatórios.'}, status=400)

        design = None
        if design_raw:
            try:
                design = json.loads(design_raw)
            except Exception:
                pass

        template = EmailTemplate.objects.create(
            organization=org,
            user=request.user,
            name=name,
            body=body,
            unlayer_design=design,
        )
        return JsonResponse({'ok': True, 'id': template.pk, 'name': template.name})

    return JsonResponse({'error': 'Método não permitido.'}, status=405)


@login_required
@require_permission('email_marketing')
def template_list(request):
    from .models import EmailTemplate
    org = get_user_organization(request.user)
    templates = EmailTemplate.objects.filter(organization=org).values('pk', 'name', 'unlayer_design')
    return JsonResponse({'templates': list(templates)})


@login_required
@require_permission('email_marketing')
def template_delete(request, pk):
    from .models import EmailTemplate
    if request.method == 'POST':
        org = get_user_organization(request.user)
        template = get_object_or_404(EmailTemplate, pk=pk, organization=org)
        template.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Método não permitido.'}, status=405)