from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organization, OrganizationMember, Invite, UserSettings


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'is_active', 'created_at']
    search_fields = ['email', 'first_name']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Dados pessoais', {'fields': ('first_name', 'last_name', 'telefone')}),
        ('Permissoes', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'email', 'created_at']
    search_fields = ['nome', 'email']


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'status', 'created_at']
    search_fields = ['user__email', 'organization__nome']


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'accepted', 'expires_at']
    search_fields = ['email', 'organization__nome']


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user']