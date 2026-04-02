from .models import OrganizationMember


def get_user_organization(user):
    if not user or not user.is_authenticated:
        return None
    membership = OrganizationMember.objects.filter(
        user=user,
        status='active'
    ).select_related('organization').first()
    return membership.organization if membership else None