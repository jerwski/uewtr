# django library
from django.contrib import admin
from django.contrib import messages

# my models
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my functions
from functions.archive import export_as_json


# Register your models here.


export_as_json.short_description = 'Eksportuj zaznaczone do JSON'


@admin.register(WorkEvidence)
class WorkEvidenceAdmin(admin.ModelAdmin):
    list_display = ('worker', 'start_work', 'end_work', 'jobhours')
    list_filter = ('worker', 'start_work')
    ordering = ['worker', '-start_work']
    actions = [export_as_json, 'aggregate']

    def aggregate(modeladmin, request, queryset):
        agg = 0
        for obj in queryset:
            agg += obj.jobhours

        msg = f'Suma godzin pracy dla zaznaczonych rekordów wynosi: {agg:,.2f} hour(s)'
        messages.success(request, msg)

    aggregate.short_description = 'Suma godzin pracy dla zaznaczonych rekordów'


@admin.register(EmployeeLeave)
class EmployeeLeaveAdmin(admin.ModelAdmin):
    list_display = ('worker','leave_date', 'leave_flag',)
    list_filter = ('worker','leave_date')
    ordering = ['worker', '-leave_date']
    actions = [export_as_json, 'aggregate']

    def aggregate(modeladmin, request, queryset):
        agg = 0
        for obj in queryset:
            agg += 8

        msg = f'Suma godzin urlopu dla zaznaczonych rekordów wynosi: {agg:,.2f} hour(s)'
        messages.success(request, msg)

    aggregate.short_description = 'Suma godzin urlopu dla zaznaczonych rekordów'


@admin.register(AccountPayment)
class AccountPaymentAdmin(admin.ModelAdmin):
    list_display = ('worker','account_date', 'account_value', 'notice')
    list_filter = ('worker', 'account_date')
    ordering = ('worker', '-account_date')
    actions = [export_as_json]
