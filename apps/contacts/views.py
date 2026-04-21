import csv
import io
import json
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import require_permission
from apps.accounts.middleware import get_user_organization
from .models import Contact, ContactGroup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sync_contacts_to_group(org, group, emails: list):
    contact_ids_to_keep = []

    for email in emails:
        email = email.strip().lower()
        if not email:
            continue
        contact, _ = Contact.objects.get_or_create(
            organization=org,
            email=email,
            defaults={'name': ''}
        )
        contact.groups.add(group)
        contact_ids_to_keep.append(contact.pk)

    to_remove = list(
        group.contacts
        .filter(email__isnull=False)
        .exclude(email='')
        .exclude(pk__in=contact_ids_to_keep)
    )
    removed = len(to_remove)
    for contact in to_remove:
        contact.groups.remove(group)

    added = group.contacts.filter(pk__in=contact_ids_to_keep).count()
    return added, removed

# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@login_required
@require_permission('contacts')
def contacts_list(request):
    org = get_user_organization(request.user)
    search_query = request.GET.get('q', '').strip()

    groups_qs = ContactGroup.objects.filter(organization=org).annotate(
        total_emails=Count(
            'contacts',
            filter=Q(contacts__email__isnull=False) & ~Q(contacts__email='')
        ),
    )

    if search_query:
        groups_qs = groups_qs.filter(name__icontains=search_query)

    paginator = Paginator(groups_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'contacts/list.html', {
        'groups': page_obj,
        'search_query': search_query,
        'page_obj': page_obj,
    })


@login_required
@require_permission('contacts')
def group_contacts_json(request, pk):
    """
    Retorna os contatos de um grupo em JSON para preencher o formulário de edição.
    Evita carregar dados sensíveis como atributos HTML no DOM.
    """
    org = get_user_organization(request.user)
    group = get_object_or_404(ContactGroup, pk=pk, organization=org)

    emails = list(
        group.contacts.filter(email__isnull=False)
        .exclude(email='')
        .values_list('email', flat=True)
    )

    data = {
        'id': group.pk,
        'name': group.name,
        'notes': group.notes or '',
        'emails': list(emails),
    }
    return JsonResponse(data)


@login_required
@require_permission('contacts')
def group_create(request):

    org = get_user_organization(request.user)
    if request.method != 'POST':
        return redirect('contacts:list')

    name = request.POST.get('name', '').strip()
    notes = request.POST.get('notes', '').strip()
    emails_raw = request.POST.get('emails', '')
    grupo_id = request.POST.get('grupo_id', '').strip()

    if not name:
        messages.error(request, 'Nome do grupo é obrigatório.')
        return redirect('contacts:list')

    emails = [e.strip().lower() for e in re.split(r'[\n\r\s,;]+', emails_raw) if e.strip()]

    if not emails:
        messages.error(request, 'Adicione ao menos um e-mail.')
        return redirect('contacts:list')

    if grupo_id:
        group = get_object_or_404(ContactGroup, pk=grupo_id, organization=org)

        if ContactGroup.objects.filter(organization=org, name=name).exclude(pk=grupo_id).exists():
            messages.error(request, f'Já existe outro grupo com o nome "{name}".')
            return redirect('contacts:list')

        group.name = name
        group.notes = notes
        group.save(update_fields=['name', 'notes'])

        added, removed = _sync_contacts_to_group(org, group, emails)
        messages.success(request, f'Grupo "{name}" atualizado. {added} contato(s), {removed} removido(s).')

    else:
        if ContactGroup.objects.filter(organization=org, name=name).exists():
            messages.error(request, f'Já existe um grupo com o nome "{name}".')
            return redirect('contacts:list')

        group = ContactGroup.objects.create(
            organization=org,
            name=name,
            notes=notes,
        )
        added, _ = _sync_contacts_to_group(org, group, emails)
        messages.success(request, f'Grupo "{name}" criado com {added} contato(s).')

    return redirect('contacts:list')


@login_required
@require_permission('contacts')
def group_delete(request, pk):
    if request.method != 'POST':
        return redirect('contacts:list')

    org = get_user_organization(request.user)
    group = get_object_or_404(ContactGroup, pk=pk, organization=org)
    name = group.name
    group.delete()
    messages.success(request, f'Grupo "{name}" excluído.')
    return redirect('contacts:list')


@login_required
@require_permission('contacts')
def import_csv(request):
    org = get_user_organization(request.user)
    if request.method != 'POST':
        return redirect('contacts:list')

    csv_file = request.FILES.get('csv_file')
    group_id = request.POST.get('group_id', '').strip()
    new_group_name = request.POST.get('new_group_name', '').strip()

    if not csv_file:
        messages.error(request, 'Selecione um arquivo CSV.')
        return redirect('contacts:list')

    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'O arquivo deve ter extensão .csv.')
        return redirect('contacts:list')

    if group_id:
        group = get_object_or_404(ContactGroup, pk=group_id, organization=org)
    elif new_group_name:
        group, _ = ContactGroup.objects.get_or_create(
            organization=org,
            name=new_group_name,
        )
    else:
        messages.error(request, 'Selecione ou crie um grupo.')
        return redirect('contacts:list')

    try:
        decoded = csv_file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        messages.error(request, 'Erro ao ler o arquivo. Certifique-se de que está em UTF-8.')
        return redirect('contacts:list')

    reader = csv.DictReader(io.StringIO(decoded))

    new_contacts = 0
    updated = 0
    skipped = 0

    for row in reader:
        email = (
            row.get('email') or row.get('Email') or row.get('EMAIL') or ''
        ).strip().lower()
        name = (
            row.get('nome') or row.get('Nome') or row.get('name') or row.get('Name') or ''
        ).strip()

        if not email or '@' not in email:
            skipped += 1
            continue

        contact, created = Contact.objects.get_or_create(
            organization=org,
            email=email,
            defaults={'name': name}
        )
        if not created:
            if name and not contact.name:
                contact.name = name
                contact.save(update_fields=['name'])
                updated += 1
        else:
            new_contacts += 1

        contact.groups.add(group)

    parts = [f'{new_contacts} novo(s)']
    if updated:
        parts.append(f'{updated} atualizado(s)')
    if skipped:
        parts.append(f'{skipped} linha(s) ignorada(s)')

    messages.success(request, f'Importação concluída: {", ".join(parts)}.')
    return redirect('contacts:list')


# ---------------------------------------------------------------------------
# Unsubscribe (público — sem login)
# ---------------------------------------------------------------------------

def unsubscribe_confirm(request, token):
    contact = get_object_or_404(Contact, unsubscribe_token=token)
    if contact.is_unsubscribed:
        return render(request, 'contacts/unsubscribe_done.html', {
            'already': True,
            'email': contact.email,
        })
    return render(request, 'contacts/unsubscribe_confirm.html', {
        'contact': contact,
        'token': token,
    })


def unsubscribe_do(request, token):
    contact = get_object_or_404(Contact, unsubscribe_token=token)
    if request.method == 'POST' and not contact.is_unsubscribed:
        contact.is_unsubscribed = True
        contact.unsubscribed_at = timezone.now()
        contact.groups.clear()
        contact.save(update_fields=['is_unsubscribed', 'unsubscribed_at'])
    return render(request, 'contacts/unsubscribe_done.html', {
        'already': False,
        'email': contact.email,
    })