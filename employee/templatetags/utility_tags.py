# standard library
from datetime import datetime

# django core
from django import template

register = template.Library()

###FILTRY###
@register.filter()
def day_since(value):
    ''' Zwraca liczbę dni między aktualną datą a podaną wartością.'''
    today = datetime.now().date()
    if isinstance(value,datetime):
        val = value.date()
    else:
        val = datetime.strptime(value,'%Y-%m-%d').date()

    diff = today - val
    if diff.days > 1:
        return '{} dni temu'.format(diff.days)
    elif diff.days == 1:
        return 'wczoraj'
    elif diff.days == 0:
        return 'dzisiaj'
    else:
        # podano przyszłą datę zwracam jako sformatowaną
        return value.__format__('%B %d. %Y')

###FILTRY###
@register.filter()
def money_format(value):
    """ Zwraca sformatowaną wartość pieniężną np.: 1,234.65 PLN """
    if value == None:
        value = 0
    elif isinstance(value, str):
        value = float(value)

    return '{:,.2f} PLN'.format(value)

###FILTRY###
# usuwa polskie znaki diakrytyczne
import unicodedata
@register.filter()
def npds(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if not unicodedata.combining(c))
