from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .middleware import get_user_organization


def require_permission(module):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            # Admin sempre tem acesso
            membership = request.user.memberships.filter(status='active').first()
            if not membership:
                messages.error(request, 'Voce nao pertence a nenhuma organizacao.')
                return redirect('dashboard')

            if membership.role == 'admin':
                return view_func(request, *args, **kwargs)

            # Verifica permissao do membro
            try:
                permissions = membership.permissions
                if not getattr(permissions, module, False):
                    messages.error(request, 'Voce nao tem permissao para acessar este modulo.')
                    return redirect('dashboard')
            except Exception:
                # Se nao tem permissoes criadas, cria com defaults
                from .models import MemberPermission
                permissions = MemberPermission.objects.create(member=membership)
                if not getattr(permissions, module, False):
                    messages.error(request, 'Voce nao tem permissao para acessar este modulo.')
                    return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator