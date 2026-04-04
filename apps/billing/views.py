from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

from apps.accounts.middleware import get_user_organization
from .models import Billing
from .services.asaas import (
    get_api_key, criar_ou_buscar_cliente,
    criar_cobranca, buscar_pix, buscar_boleto
)


@login_required
def billing_list(request):
    org = get_user_organization(request.user)
    status_filter = request.GET.get('status', '')
    billings = Billing.objects.filter(organization=org)
    if status_filter:
        billings = billings.filter(status=status_filter)

    totais = {
        'total': billings.count(),
        'pendente': billings.filter(status='PENDING').count(),
        'pago': billings.filter(status__in=['RECEIVED', 'CONFIRMED']).count(),
        'vencido': billings.filter(status='OVERDUE').count(),
    }

    return render(request, 'billing/list.html', {
        'billings': billings,
        'totais': totais,
        'status_filter': status_filter,
    })


@login_required
def billing_create(request):
    org = get_user_organization(request.user)

    if request.method == 'POST':
        api_key = get_api_key(org)
        if not api_key:
            messages.error(request, 'Configure a API Key do Asaas nas configurações.')
            return redirect('billing:list')

        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email', '')
        customer_phone = request.POST.get('customer_phone', '')
        customer_cpf_cnpj = request.POST.get('customer_cpf_cnpj', '')
        description = request.POST.get('description')
        value = request.POST.get('value')
        due_date_str = request.POST.get('due_date')
        payment_method = request.POST.get('payment_method', 'PIX')
        notify_via = request.POST.get('notify_via', 'email')

        from datetime import date
        due_date = date.fromisoformat(due_date_str)

        customer_id, err = criar_ou_buscar_cliente(
            api_key, customer_name, customer_cpf_cnpj, customer_email, customer_phone
        )
        if not customer_id:
            messages.error(request, f'Erro ao criar cliente no Asaas: {err}')
            return redirect('billing:create')

        payment, err = criar_cobranca(api_key, customer_id, value, due_date, description, payment_method)
        if not payment:
            messages.error(request, f'Erro ao criar cobrança no Asaas: {err}')
            return redirect('billing:create')

        billing = Billing.objects.create(
            organization=org,
            user=request.user,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_cpf_cnpj=customer_cpf_cnpj,
            description=description,
            value=value,
            due_date=due_date,
            payment_method=payment_method,
            notify_via=notify_via,
            asaas_id=payment.get('id'),
            asaas_url=payment.get('invoiceUrl'),
            status=payment.get('status', 'PENDING'),
        )

        if payment_method == 'PIX':
            pix_data, _ = buscar_pix(api_key, payment['id'])
            if pix_data:
                billing.pix_qrcode = pix_data.get('encodedImage')
                billing.pix_payload = pix_data.get('payload')
                billing.save()

        if payment_method == 'BOLETO':
            boleto_data, _ = buscar_boleto(api_key, payment['id'])
            if boleto_data:
                billing.boleto_code = boleto_data.get('identificationField')
                billing.boleto_url = payment.get('bankSlipUrl')
                billing.save()

        if notify_via in ['email', 'both'] and customer_email:
            try:
                from apps.mailer.services import send_campaign_email
                send_campaign_email(
                    to=[customer_email],
                    subject=f'Cobrança: {description}',
                    body=f'''
                        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
                            <h2 style="color:#111;">Olá, {customer_name}!</h2>
                            <p>Você tem uma cobrança de <strong>R$ {value}</strong> com vencimento em <strong>{due_date.strftime("%d/%m/%Y")}</strong>.</p>
                            <p><strong>Descrição:</strong> {description}</p>
                            <p style="margin-top:24px;">
                                <a href="{billing.asaas_url}" style="background:#111;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:500;">
                                    Pagar agora
                                </a>
                            </p>
                        </div>
                    ''',
                    user=request.user,
                )
            except Exception as e:
                print(f'Erro ao enviar e-mail de cobrança: {e}')

        messages.success(request, f'Cobrança criada com sucesso para {customer_name}!')
        return redirect('billing:detail', pk=billing.pk)

    return render(request, 'billing/create.html')


@login_required
def billing_detail(request, pk):
    org = get_user_organization(request.user)
    billing = get_object_or_404(Billing, pk=pk, organization=org)
    return render(request, 'billing/detail.html', {'billing': billing})


@csrf_exempt
def billing_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event = data.get('event')
            payment = data.get('payment', {})
            asaas_id = payment.get('id')

            print(f'WEBHOOK RECEBIDO: event={event}, asaas_id={asaas_id}')

            status_map = {
                'PAYMENT_RECEIVED': 'RECEIVED',
                'PAYMENT_CONFIRMED': 'CONFIRMED',
                'PAYMENT_OVERDUE': 'OVERDUE',
                'PAYMENT_REFUNDED': 'REFUNDED',
                'PAYMENT_CANCELLED': 'CANCELLED',
            }

            new_status = status_map.get(event)
            if new_status and asaas_id:
                updated = Billing.objects.filter(asaas_id=asaas_id).update(status=new_status)
                print(f'WEBHOOK: status atualizado para {new_status}, registros={updated}')

        except Exception as e:
            print(f'WEBHOOK ERRO: {e}')

    return HttpResponse(status=200)