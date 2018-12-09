# standard library
import os

# django library
from django.contrib import admin
from django.contrib import messages
from django.core import serializers

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate


# Register your models here.

# serialization json
def export_as_json(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    path = os.path.join(r'backup_json/{}.json')
    with open(path.format(opts.verbose_name), 'w') as outfile:
        json_serializer = serializers.get_serializer('json')()
        json_serializer.serialize(queryset, stream=outfile, indent=4)
    messages.success(request, 'Rekordy zapisane do pliku {}'.format(path.format(opts.verbose_name)))

export_as_json.short_description = 'Eksportuj zaznaczone do JSON'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('surname', 'forename', 'pesel', 'status')
    list_filter = ('surname', 'forename')
    list_editable = ('status',)
    ordering = ['surname']
    actions = [export_as_json]


@admin.register(EmployeeData)
class EmployeeDataAdmin(admin.ModelAdmin):
    list_display = ('name','birthday', 'postal', 'city', 'street', 'house', 'flat', 'phone',)
    list_filter = ('name',)
    ordering = ['name']
    actions = [export_as_json]

    fieldsets = [('Employee', {'fields': ('name', 'workplace','start_contract', 'end_contract', 'overtime',)}),
                 ('Extended Data', {'classes': ('collapse',),
                                    'fields': ('birthday', 'postal', 'city', 'street', 'house', 'flat', 'phone',)}),]


@admin.register(EmployeeHourlyRate)
class EmployeeHourlyRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'update', 'hourly_rate')
    list_filter = ('name',)
    ordering = ['name']
    actions = [export_as_json]