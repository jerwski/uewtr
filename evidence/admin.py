# django library
from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

# my models
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my functions
from functions.archive import export_as_json


# Register your models here.


export_as_json.short_description = 'Export selected records to json file'



class LastMonthWorkingDaysFilter(admin.SimpleListFilter):
    title = _('last month')
    parameter_name = 'month_year'

    def lookups(self, request, model_admin):
        year, month = timezone.now().year, timezone.now().month
        if month == 1:
            year, month = year-1, 12
        else:
            year, month = year, month-1

        qs = model_admin.get_queryset(request)
        if qs.filter(start_work__year=year, start_work__month=month).exists():
            yield (f'{month}/{year}',_('Last month'))


    def queryset(self, request, queryset):
        if self.value():
            year, month = timezone.now().year, timezone.now().month
            if month == 1:
                year, month = year-1, 12
            else:
                year, month = year, month-1
            return queryset.filter(start_work__year=year, start_work__month=month)
        else:
            return queryset


@admin.register(WorkEvidence)
class WorkEvidenceAdmin(admin.ModelAdmin):
    list_display = ('worker', 'start_work', 'end_work', 'jobhours')
    list_filter = ('worker', 'start_work', LastMonthWorkingDaysFilter)
    ordering = ['worker', '-start_work']
    actions = [export_as_json, 'aggregate', 'working_days']

    def aggregate(self, request, queryset):
        agg = 0
        for obj in queryset:
            agg += obj.jobhours

        msg = f'The sum of working hours for the selected records is: {agg:,.2f} hour(s)'
        messages.success(request, msg)

    aggregate.short_description = 'Sum of working hours for the selected records'


@admin.register(EmployeeLeave)
class EmployeeLeaveAdmin(admin.ModelAdmin):
    list_display = ('worker','leave_date', 'leave_flag',)
    list_filter = ('worker','leave_date')
    ordering = ['worker', '-leave_date']
    actions = [export_as_json, 'aggregate']

    def aggregate(self, request, queryset):
        agg = 0
        for obj in queryset:
            agg += 8

        msg = f'The sum of hours of leave for selected records is: {agg:,.2f} hour(s)'
        messages.success(request, msg)

    aggregate.short_description = 'Sum of hours of leave for the selected records'


@admin.register(AccountPayment)
class AccountPaymentAdmin(admin.ModelAdmin):
    list_display = ('worker','account_date', 'account_value', 'notice')
    list_filter = ('worker', 'account_date')
    ordering = ('worker', '-account_date')
    actions = [export_as_json]
