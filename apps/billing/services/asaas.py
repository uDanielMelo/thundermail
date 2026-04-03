import requests
from django.conf import settings


ASAAS_BASE_URL = getattr(settings, 'ASAAS_BASE_URL', 'https://sandbox.asaas.com/api/v3')


def get_headers(api_key):
    return {
        'accept': 'application/json',
        'content-type': 'application/json',
        'access_token': api_key,
    }


def get_api_key(organization):
    return getattr(organization, 'asaas_api_key', None) or settings.ASAAS_API_KEY


def criar_ou_buscar_cliente(api_key, name, cpf_cnpj=None, email=None, phone=None):
    headers = get_headers(api_key)

    # Busca cliente existente pelo CPF/CNPJ
    if cpf_cnpj:
        cpf_cnpj_clean = ''.join(filter(str.isdigit, cpf_cnpj))
        resp = requests.get(
            f'{ASAAS_BASE_URL}/customers',
            headers=headers,
            params={'cpfCnpj': cpf_cnpj_clean}
        )
        if resp.ok:
            data = resp.json()
            if data.get('data'):
                return data['data'][0]['id'], None

    # Cria novo cliente
    payload = {'name': name}
    if cpf_cnpj:
        payload['cpfCnpj'] = ''.join(filter(str.isdigit, cpf_cnpj))
    if email:
        payload['email'] = email
    if phone:
        payload['mobilePhone'] = ''.join(filter(str.isdigit, phone))

    resp = requests.post(f'{ASAAS_BASE_URL}/customers', headers=headers, json=payload)
    if resp.ok:
        return resp.json()['id'], None
    return None, resp.json()


def criar_cobranca(api_key, customer_id, value, due_date, description, payment_method):
    headers = get_headers(api_key)

    billing_type_map = {
        'PIX': 'PIX',
        'BOLETO': 'BOLETO',
        'CREDIT_CARD': 'CREDIT_CARD',
    }

    payload = {
        'customer': customer_id,
        'billingType': billing_type_map.get(payment_method, 'PIX'),
        'value': float(value),
        'dueDate': due_date.strftime('%Y-%m-%d'),
        'description': description,
    }

    resp = requests.post(f'{ASAAS_BASE_URL}/payments', headers=headers, json=payload)
    if resp.ok:
        return resp.json(), None
    return None, resp.json()


def buscar_pix(api_key, payment_id):
    headers = get_headers(api_key)
    resp = requests.get(f'{ASAAS_BASE_URL}/payments/{payment_id}/pixQrCode', headers=headers)
    if resp.ok:
        return resp.json(), None
    return None, resp.json()


def buscar_boleto(api_key, payment_id):
    headers = get_headers(api_key)
    resp = requests.get(f'{ASAAS_BASE_URL}/payments/{payment_id}/identificationField', headers=headers)
    if resp.ok:
        return resp.json(), None
    return None, resp.json()


def buscar_status(api_key, payment_id):
    headers = get_headers(api_key)
    resp = requests.get(f'{ASAAS_BASE_URL}/payments/{payment_id}', headers=headers)
    if resp.ok:
        return resp.json().get('status'), None
    return None, resp.json()