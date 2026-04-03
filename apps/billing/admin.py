from django.contrib import admin
from .models import Billing

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'value', 'payment_method', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['customer_name', 'customer_email', 'asaas_id']