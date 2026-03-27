from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Contract, ContractSigner
from apps.mailer.services import send_campaign_email


@login_required
def contracts_list(request):
    contracts = Contract.objects.filter(user=request.user)
    return render(request, 'contracts/list.html', {'contracts': contracts})


@login_required
def contract_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message', '')
        document = request.FILES.get('document')

        if not title or not document:
            messages.error(request, 'Título e documento são obrigatórios.')
            return render(request, 'contracts/create.html')

        if not document.name.endswith('.pdf'):
            messages.error(request, 'Apenas arquivos PDF são aceitos.')
            return render(request, 'contracts/create.html')

        contract = Contract.objects.create(
            user=request.user,
            title=title,
            message=message,
            document=document,
        )

        # Adiciona signatários
        names = request.POST.getlist('signer_name')
        emails = request.POST.getlist('signer_email')
        cpfs = request.POST.getlist('signer_cpf')

        for i, email in enumerate(emails):
            if email.strip():
                ContractSigner.objects.create(
                    contract=contract,
                    name=names[i] if i < len(names) else '',
                    email=email.strip(),
                    cpf=cpfs[i] if i < len(cpfs) else '',
                )

        messages.success(request, f'Contrato "{title}" criado com sucesso!')
        return redirect('contracts:detail', pk=contract.pk)

    return render(request, 'contracts/create.html')


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk, user=request.user)
    return render(request, 'contracts/detail.html', {'contract': contract})


@login_required
def contract_send(request, pk):
    contract = get_object_or_404(Contract, pk=pk, user=request.user)

    if request.method == 'POST':
        if contract.status not in ['rascunho']:
            messages.error(request, 'Este contrato já foi enviado.')
            return redirect('contracts:detail', pk=pk)

        if not contract.signers.exists():
            messages.error(request, 'Adicione ao menos um signatário antes de enviar.')
            return redirect('contracts:detail', pk=pk)

        sent = 0
        for signer in contract.signers.all():
            sign_url = signer.get_sign_url()
            body = f"""
            <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
                <h2 style="color:#111;">Você recebeu um contrato para assinar</h2>
                <p>Olá, <strong>{signer.name}</strong>!</p>
                <p>{contract.message or 'Por favor, revise e assine o contrato abaixo.'}</p>
                <p><strong>Contrato:</strong> {contract.title}</p>
                <div style="margin:32px 0;">
                    <a href="{sign_url}"
                       style="background:#111;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;">
                        Visualizar e Assinar
                    </a>
                </div>
                <p style="font-size:12px;color:#999;">
                    Este link é único e intransferível. Ao assinar você concorda com os termos do documento.
                </p>
            </div>
            """
            result = send_campaign_email(
                to=[signer.email],
                subject=f'[Assinatura] {contract.title}',
                body=body,
            )
            if result['success']:
                sent += 1

        contract.status = 'enviado'
        contract.save()

        messages.success(request, f'Contrato enviado para {sent} signatário(s).')
        return redirect('contracts:detail', pk=pk)

    return redirect('contracts:detail', pk=pk)


@login_required
def contract_cancel(request, pk):
    contract = get_object_or_404(Contract, pk=pk, user=request.user)
    if request.method == 'POST':
        contract.status = 'cancelado'
        contract.save()
        messages.success(request, 'Contrato cancelado.')
    return redirect('contracts:detail', pk=pk)


@login_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk, user=request.user)
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contrato deletado.')
        return redirect('contracts:list')
    return redirect('contracts:detail', pk=pk)


# ─────────────────────────────────────────
# ASSINATURA — público, sem login
# ─────────────────────────────────────────

def sign_view(request, token):
    signer = get_object_or_404(ContractSigner, token=token)

    if signer.status == 'assinado':
        return redirect('contracts:sign_done', token=token)

    if signer.contract.status == 'cancelado':
        return render(request, 'contracts/sign_cancelled.html', {'signer': signer})

    # Marca como visualizado
    if signer.status == 'pendente':
        signer.status = 'visualizado'
        signer.save()

    return render(request, 'contracts/sign.html', {
        'signer': signer,
        'contract': signer.contract,
    })


def sign_confirm(request, token):
    signer = get_object_or_404(ContractSigner, token=token)

    if request.method == 'POST':
        if signer.status == 'assinado':
            return redirect('contracts:sign_done', token=token)

        signature_data = request.POST.get('signature_data', '')

        if not signature_data:
            messages.error(request, 'A assinatura é obrigatória.')
            return redirect('contracts:sign', token=token)

        # Captura IP real
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        signer.status = 'assinado'
        signer.signed_at = timezone.now()
        signer.ip_address = ip
        signer.user_agent = request.META.get('HTTP_USER_AGENT', '')
        signer.signature_data = signature_data
        signer.save()

        # Verifica se todos assinaram
        contract = signer.contract
        if contract.is_complete():
            contract.status = 'concluido'
            contract.save()
        elif contract.signed_count() > 0:
            contract.status = 'parcial'
            contract.save()

        return redirect('contracts:sign_done', token=token)

    return redirect('contracts:sign', token=token)


def sign_decline(request, token):
    signer = get_object_or_404(ContractSigner, token=token)

    if request.method == 'POST':
        signer.status = 'recusado'
        signer.save()

    return render(request, 'contracts/sign_declined.html', {'signer': signer})


def sign_done(request, token):
    signer = get_object_or_404(ContractSigner, token=token)
    return render(request, 'contracts/sign_done.html', {'signer': signer})


@login_required
def contract_download(request, pk):
    from django.http import HttpResponse
    from .services.pdf_service import merge_pdf_with_audit

    contract = get_object_or_404(Contract, pk=pk, user=request.user)

    if contract.status not in ['concluido', 'parcial', 'enviado']:
        messages.error(request, 'Contrato não disponível para download.')
        return redirect('contracts:detail', pk=pk)

    pdf = merge_pdf_with_audit(contract)

    response = HttpResponse(pdf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{contract.title}_assinado.pdf"'
    return response