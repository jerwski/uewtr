# django library
from django.contrib import admin

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate

# my functions
from functions.archive import export_as_json


# Register your models here.


export_as_json.short_description = 'Export selected records to json file'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('surname', 'forename', 'pesel', 'status')
    list_filter = ('surname', 'forename')
    list_editable = ('status',)
    ordering = ['surname']
    actions = [export_as_json]


@admin.register(EmployeeData)
class EmployeeDataAdmin(admin.ModelAdmin):
    list_display = ('worker','birthday', 'postal', 'city', 'street', 'house', 'flat', 'phone',)
    list_filter = ('worker',)
    ordering = ['worker']
    actions = [export_as_json]

    fieldsets = [('Employee', {'fields': ('worker', 'workplace','start_contract', 'end_contract', 'overtime',)}),
                 ('Extended Data', {'classes': ('collapse',),
                                    'fields': ('birthday', 'postal', 'city', 'street', 'house', 'flat', 'phone',)}),]


@admin.register(EmployeeHourlyRate)
class EmployeeHourlyRateAdmin(admin.ModelAdmin):
    list_display = ('worker', 'update', 'hourly_rate')
    list_filter = ('worker',)
    ordering = ['worker']
    actions = [export_as_json]