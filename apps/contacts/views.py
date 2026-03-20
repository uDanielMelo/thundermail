from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Contact, ContactGroup


@login_required
def contacts_list(request):
    search_query = request.GET.get('q', '')
    groups = ContactGroup.objects.filter(user=request.user)
    if search_query:
        groups = groups.filter(name__icontains=search_query)
    return render(request, 'contacts/list.html', {
        'groups': groups,
        'search_query': search_query
    })


@login_required
def group_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        notes = request.POST.get('notes')
        emails_raw = request.POST.get('emails', '')

        if not name:
            messages.error(request, 'Nome do grupo é obrigatório.')
            return redirect('contacts:list')

        if ContactGroup.objects.filter(user=request.user, name=name).exists():
            messages.error(request, 'Já existe um grupo com esse nome.')
            return redirect('contacts:list')

        group = ContactGroup.objects.create(
            user=request.user,
            name=name,
            notes=notes
        )

        emails = [e.strip() for e in emails_raw.splitlines() if e.strip()]
        for email in emails:
            contact, _ = Contact.objects.get_or_create(
                user=request.user,
                email=email
            )
            contact.group = group
            contact.save()

        messages.success(request, f'Grupo "{name}" criado com {len(emails)} contatos.')
        return redirect('contacts:list')

    return redirect('contacts:list')


@login_required
def group_delete(request, pk):
    group = get_object_or_404(ContactGroup, pk=pk, user=request.user)
    group.delete()
    messages.success(request, 'Grupo deletado com sucesso.')
    return redirect('contacts:list')