from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from apps.accounts.middleware import get_user_organization
from .models import Project, Task, TaskComment


@login_required
def tasks_home(request):
    org = get_user_organization(request.user)
    projects = Project.objects.filter(organization=org)

    # Redireciona para o primeiro projeto ou mostra tela vazia
    if projects.exists():
        return redirect('tasks:project_detail', pk=projects.first().pk)

    return render(request, 'tasks/home.html', {'projects': projects})


@login_required
def project_detail(request, pk):
    org = get_user_organization(request.user)
    project = get_object_or_404(Project, pk=pk, organization=org)
    projects = Project.objects.filter(organization=org)

    tasks_todo = project.tasks.filter(status='todo')
    tasks_doing = project.tasks.filter(status='doing')
    tasks_done = project.tasks.filter(status='done')

    # Membros ativos da organização
    from apps.accounts.models import OrganizationMember
    members = OrganizationMember.objects.filter(
        organization=org,
        status='active'
    ).select_related('user')

    return render(request, 'tasks/kanban.html', {
        'project': project,
        'projects': projects,
        'tasks_todo': tasks_todo,
        'tasks_doing': tasks_doing,
        'tasks_done': tasks_done,
        'members': members,
    })


@login_required
@require_POST
def project_create(request):
    org = get_user_organization(request.user)
    name = request.POST.get('name')
    color = request.POST.get('color', '#378ADD')

    if not name:
        messages.error(request, 'Nome do projeto é obrigatório.')
        return redirect('tasks:home')

    project = Project.objects.create(
        organization=org,
        user=request.user,
        name=name,
        color=color,
    )
    return redirect('tasks:project_detail', pk=project.pk)


@login_required
@require_POST
def project_delete(request, pk):
    org = get_user_organization(request.user)
    project = get_object_or_404(Project, pk=pk, organization=org)
    project.delete()
    messages.success(request, 'Projeto deletado.')
    return redirect('tasks:home')


@login_required
@require_POST
def task_create(request):
    org = get_user_organization(request.user)
    project_id = request.POST.get('project_id')
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    priority = request.POST.get('priority', 'medium')
    due_date = request.POST.get('due_date') or None
    status = request.POST.get('status', 'todo')
    assigned_to_id = request.POST.get('assigned_to') or None

    project = get_object_or_404(Project, pk=project_id, organization=org)

    assigned_to = None
    if assigned_to_id:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            assigned_to = User.objects.get(pk=assigned_to_id)
        except User.DoesNotExist:
            pass

    task = Task.objects.create(
        project=project,
        organization=org,
        created_by=request.user,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        status=status,
        assigned_to=assigned_to,
    )

    # Notificação por e-mail se atribuída a alguém
    if assigned_to and assigned_to != request.user:
        _notify_task_assigned(task, assigned_to, request.user)

    return redirect('tasks:project_detail', pk=project.pk)

def _notify_task_assigned(task, assigned_to, assigned_by):
    try:
        from apps.mailer.services import send_campaign_email
        send_campaign_email(
            to=[assigned_to.email],
            subject=f'Nova tarefa atribuída: {task.title}',
            body=f'''
                <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
                    <h2 style="color:#111;">Você tem uma nova tarefa!</h2>
                    <p><strong>{assigned_by.get_full_name() or assigned_by.email}</strong> atribuiu uma tarefa para você:</p>
                    <div style="background:#f9f9f9;border-left:4px solid #111;padding:12px 16px;margin:16px 0;border-radius:4px;">
                        <p style="font-size:16px;font-weight:500;margin:0;">{task.title}</p>
                        {"<p style='color:#666;margin:8px 0 0;'>"+task.description+"</p>" if task.description else ""}
                    </div>
                    <table style="font-size:14px;color:#666;">
                        <tr><td style="padding:4px 12px 4px 0;">Projeto</td><td><strong>{task.project.name}</strong></td></tr>
                        <tr><td style="padding:4px 12px 4px 0;">Prioridade</td><td><strong>{task.get_priority_display()}</strong></td></tr>
                        {"<tr><td style='padding:4px 12px 4px 0;'>Vencimento</td><td><strong>"+str(task.due_date.strftime('%d/%m/%Y'))+"</strong></td></tr>" if task.due_date else ""}
                    </table>
                </div>
            ''',
            user=assigned_by,
        )
    except Exception as e:
        print(f'Erro ao notificar tarefa: {e}')

@login_required
def task_detail(request, pk):
    org = get_user_organization(request.user)
    task = get_object_or_404(Task, pk=pk, organization=org)
    projects = Project.objects.filter(organization=org)
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'projects': projects,
    })


@login_required
def task_update_status(request, pk):
    org = get_user_organization(request.user)
    task = get_object_or_404(Task, pk=pk, organization=org)

    if request.method == 'POST':
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in ['todo', 'doing', 'done']:
            task.status = new_status
            task.save()
            return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


@login_required
@require_POST
def task_delete(request, pk):
    org = get_user_organization(request.user)
    task = get_object_or_404(Task, pk=pk, organization=org)
    project_pk = task.project.pk
    task.delete()
    return redirect('tasks:project_detail', pk=project_pk)


@login_required
@require_POST
def task_comment(request, pk):
    org = get_user_organization(request.user)
    task = get_object_or_404(Task, pk=pk, organization=org)
    content = request.POST.get('content')

    if content:
        TaskComment.objects.create(task=task, user=request.user, content=content)

    return redirect('tasks:task_detail', pk=task.pk)