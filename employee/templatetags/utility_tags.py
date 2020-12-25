# standard library
from datetime import datetime

# django core
from django import template
from django.urls import reverse


# Create your tags and filters here.


register = template.Library()


###FILTER###
@register.filter()
def day_since(target_date):
	''' Returns the number of days between the current date and the target date'''
	today = datetime.now().date()
	if isinstance(target_date, datetime):
		val = target_date.date()
	else:
		val = datetime.strptime(target_date,'%Y-%m-%d').date()

	diff = today - val
	if diff.days > 1:
		return f'{diff.days} dni temu'
	elif diff.days == 1:
		return 'wczoraj'
	elif diff.days == 0:
		return 'dzisiaj'
	else:
		return target_date.__format__('%B %d. %Y')


###FILTER###
@register.filter()
def money_format(value):
	# print(f'Zmienna: {value} => typ zmiennej to {type(value)}')
	""" Returns the formatted monetary value e.g. 1,234.65 PLN """
	if value == None:
		value = 0
	elif isinstance(value, str):
		value = float(value)

	return f'{value:,.2f} PLN'


###FILTER###
# removes Polish diacritics
import unicodedata
@register.filter()
def npds(txt):
	return ''.join(c for c in unicodedata.normalize('NFD', txt) if not unicodedata.combining(c))


@register.simple_tag()
def employee_complex_data_pass(employee_id:int, month:int, year:int):
	return reverse('evidence:employee_complex_data_args', args=[employee_id, month, year])
