from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Contact, ContactGroup
from django.utils import timezone
from apps.accounts.middleware import get_user_organization
from apps.accounts.decorators import require_permission


@login_required
@require_permission('contacts')
def contacts_list(request):
    org = get_user_organization(request.user)
    search_query = request.GET.get('q', '')
    groups = ContactGroup.objects.filter(organization=org)
    if search_query:
        groups = groups.filter(name__icontains=search_query)
    return render(request, 'contacts/list.html', {
        'groups': groups,
        'search_query': search_query
    })


@login_required
@require_permission('contacts')
def group_create(request):
    org = get_user_organization(request.user)
    if request.method == 'POST':
        name = request.POST.get('name')
        notes = request.POST.get('notes')
        emails_raw = request.POST.get('emails', '')

        if not name:
            messages.error(request, 'Nome do grupo e obrigatorio.')
            return redirect('contacts:list')

        if ContactGroup.objects.filter(organization=org, name=name).exists():
            messages.error(request, 'Ja existe um grupo com esse nome.')
            return redirect('contacts:list')

        group = ContactGroup.objects.create(
            organization=org,
            user=request.user,
            name=name,
            notes=notes
        )

        emails = [e.strip() for e in emails_raw.splitlines() if e.strip()]
        for email in emails:
            contact, _ = Contact.objects.get_or_create(
                organization=org,
                email=email,
                defaults={'user': request.user}
            )
            contact.group = group
            contact.save()

        messages.success(request, f'Grupo "{name}" criado com {len(emails)} contatos.')
        return redirect('contacts:list')

    return redirect('contacts:list')


@login_required
@require_permission('contacts')
def group_delete(request, pk):
    org = get_user_organization(request.user)
    group = get_object_or_404(ContactGroup, pk=pk, organization=org)
    group.delete()
    messages.success(request, 'Grupo deletado com sucesso.')
    return redirect('contacts:list')


@login_required
@require_permission('contacts')
def import_csv(request):
    org = get_user_organization(request.user)
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        group_id = request.POST.get('group_id')
        new_group_name = request.POST.get('new_group_name', '')

        if not csv_file:
            messages.error(request, 'Selecione um arquivo CSV.')
            return redirect('contacts:list')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'O arquivo deve ser .csv')
            return redirect('contacts:list')

        if group_id:
            group = get_object_or_404(ContactGroup, pk=group_id, organization=org)
        elif new_group_name:
            group, _ = ContactGroup.objects.get_or_create(
                organization=org,
                name=new_group_name,
                defaults={'user': request.user}
            )
        else:
            messages.error(request, 'Selecione ou crie um grupo.')
            return redirect('contacts:list')

        import csv
        import io

        decoded = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))

        total = 0
        erros = 0
        duplicados = 0

        for row in reader:
            email = (row.get('email') or row.get('Email') or row.get('EMAIL') or '').strip()
            name = (row.get('nome') or row.get('Nome') or row.get('name') or row.get('Name') or '').strip()
            phone = (row.get('telefone') or row.get('Telefone') or row.get('phone') or '').strip()

            if not email or '@' not in email:
                erros += 1
                continue

            contact, created = Contact.objects.get_or_create(
                organization=org,
                email=email,
                defaults={'user': request.user, 'name': name, 'phone': phone}
            )

            if not created:
                duplicados += 1
            else:
                total += 1

            contact.group = group
            contact.save()

        messages.success(request, f'Importacao concluida! {total} novos, {duplicados} duplicados, {erros} erros.')
        return redirect('contacts:list')

    return redirect('contacts:list')


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

    if request.method == 'POST':
        if not contact.is_unsubscribed:
            contact.is_unsubscribed = True
            contact.unsubscribed_at = timezone.now()
            contact.group = None
            contact.save()

    return render(request, 'contacts/unsubscribe_done.html', {
        'already': False,
        'email': contact.email,
    })