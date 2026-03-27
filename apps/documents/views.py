from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Document, Folder, Tag


@login_required
def documents_home(request):
    q = request.GET.get('q', '')
    folder_id = request.GET.get('folder', '')
    tag_id = request.GET.get('tag', '')
    doc_type = request.GET.get('type', '')
    favorites = request.GET.get('favorites', '')
    view_mode = request.GET.get('view', 'list')

    documents = Document.objects.filter(user=request.user)
    folders = Folder.objects.filter(user=request.user, parent=None)
    tags = Tag.objects.filter(user=request.user)

    if q:
        documents = documents.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(content__icontains=q)
        )
    if folder_id:
        documents = documents.filter(folder_id=folder_id)
    if tag_id:
        documents = documents.filter(tags__id=tag_id)
    if doc_type:
        documents = documents.filter(doc_type=doc_type)
    if favorites:
        documents = documents.filter(is_favorite=True)

    current_folder = None
    if folder_id:
        current_folder = Folder.objects.filter(pk=folder_id, user=request.user).first()

    return render(request, 'documents/home.html', {
        'documents': documents,
        'folders': folders,
        'tags': tags,
        'q': q,
        'folder_id': folder_id,
        'tag_id': tag_id,
        'doc_type': doc_type,
        'favorites': favorites,
        'view_mode': view_mode,
        'current_folder': current_folder,
        'total': documents.count(),
        'tag_colors': Tag.COLORS,
        'folder_colors': ['#6b7280', '#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#a855f7', '#ec4899'],
    })


@login_required
def folder_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#6b7280')
        parent_id = request.POST.get('parent_id')

        if not name:
            messages.error(request, 'Nome da pasta é obrigatório.')
            return redirect('documents:home')

        Folder.objects.get_or_create(
            user=request.user,
            name=name,
            parent_id=parent_id or None,
            defaults={'color': color}
        )
        messages.success(request, f'Pasta "{name}" criada.')
    return redirect('documents:home')


@login_required
def folder_delete(request, pk):
    folder = get_object_or_404(Folder, pk=pk, user=request.user)
    if request.method == 'POST':
        folder.delete()
        messages.success(request, 'Pasta deletada.')
    return redirect('documents:home')


@login_required
def document_upload(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '')
        folder_id = request.POST.get('folder_id') or None
        tag_ids = request.POST.getlist('tags')
        file = request.FILES.get('file')

        if not title or not file:
            messages.error(request, 'Título e arquivo são obrigatórios.')
            return redirect('documents:home')

        doc = Document.objects.create(
            user=request.user,
            title=title,
            description=description,
            folder_id=folder_id,
            doc_type='file',
            file=file,
            file_size=file.size,
        )
        if tag_ids:
            doc.tags.set(tag_ids)

        messages.success(request, f'"{title}" enviado com sucesso.')
        return redirect('documents:detail', pk=doc.pk)

    folders = Folder.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    return render(request, 'documents/upload.html', {'folders': folders, 'tags': tags})


@login_required
def document_note(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '')
        description = request.POST.get('description', '')
        folder_id = request.POST.get('folder_id') or None
        tag_ids = request.POST.getlist('tags')

        if not title:
            messages.error(request, 'Título é obrigatório.')
            return redirect('documents:home')

        doc = Document.objects.create(
            user=request.user,
            title=title,
            content=content,
            description=description,
            folder_id=folder_id,
            doc_type='note',
        )
        if tag_ids:
            doc.tags.set(tag_ids)

        messages.success(request, f'Nota "{title}" salva.')
        return redirect('documents:detail', pk=doc.pk)

    folders = Folder.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    return render(request, 'documents/note.html', {'folders': folders, 'tags': tags})


@login_required
def document_link(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        url = request.POST.get('url', '').strip()
        description = request.POST.get('description', '')
        folder_id = request.POST.get('folder_id') or None
        tag_ids = request.POST.getlist('tags')

        if not title or not url:
            messages.error(request, 'Título e URL são obrigatórios.')
            return redirect('documents:home')

        doc = Document.objects.create(
            user=request.user,
            title=title,
            url=url,
            description=description,
            folder_id=folder_id,
            doc_type='link',
        )
        if tag_ids:
            doc.tags.set(tag_ids)

        messages.success(request, f'Link "{title}" salvo.')
        return redirect('documents:detail', pk=doc.pk)

    folders = Folder.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    return render(request, 'documents/link.html', {'folders': folders, 'tags': tags})


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    return render(request, 'documents/detail.html', {'doc': doc})


@login_required
def document_edit(request, pk):
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    folders = Folder.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)

    if request.method == 'POST':
        doc.title = request.POST.get('title', doc.title).strip()
        doc.description = request.POST.get('description', '')
        doc.folder_id = request.POST.get('folder_id') or None
        tag_ids = request.POST.getlist('tags')

        if doc.doc_type == 'note':
            doc.content = request.POST.get('content', '')
        elif doc.doc_type == 'link':
            doc.url = request.POST.get('url', '')

        doc.save()
        if tag_ids:
            doc.tags.set(tag_ids)
        else:
            doc.tags.clear()

        messages.success(request, 'Documento atualizado.')
        return redirect('documents:detail', pk=doc.pk)

    return render(request, 'documents/edit.html', {
        'doc': doc,
        'folders': folders,
        'tags': tags,
    })


@login_required
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Documento deletado.')
        return redirect('documents:home')
    return redirect('documents:detail', pk=pk)


@login_required
def document_favorite(request, pk):
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    doc.is_favorite = not doc.is_favorite
    doc.save()
    return redirect(request.META.get('HTTP_REFERER', 'documents:home'))


@login_required
def tag_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', 'gray')

        if not name:
            messages.error(request, 'Nome da tag é obrigatório.')
            return redirect('documents:home')

        Tag.objects.get_or_create(user=request.user, name=name, defaults={'color': color})
        messages.success(request, f'Tag "{name}" criada.')
    return redirect('documents:home')


@login_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deletada.')
    return redirect('documents:home')