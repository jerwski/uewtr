# standard library
import os

# django library
from django.contrib import admin
from django.contrib import messages
from django.core import serializers

# my models
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment


# Register your models here.


# serialization json
def export_as_json(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    path = os.path.join(os.curdir, r'backup_json/{}.json')
    with open(path.format(opts.verbose_name), 'w') as outfile:
        json_serializer = serializers.get_serializer('json')()
        json_serializer.serialize(queryset, stream=outfile, indent=4)
    messages.success(request, 'Rekordy zapisane do pliku {}'.format(path.format(opts.verbose_name)))

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

        msg = r'Suma godzin pracy dla zaznaczonych rekordów wynosi: {:,.2f} hour(s)'
        messages.success(request, msg.format(agg))

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

        msg = r'Suma godzin urlopu dla zaznaczonych rekordów wynosi: {:,.2f} hour(s)'
        messages.success(request, msg.format(agg))

    aggregate.short_description = 'Suma godzin urlopu dla zaznaczonych rekordów'


@admin.register(AccountPayment)
class AccountPaymentAdmin(admin.ModelAdmin):
    list_display = ('worker','account_date', 'account_value', 'notice')
    list_filter = ('worker', 'account_date')
    ordering = ('worker', '-account_date')
    actions = [export_as_json]
