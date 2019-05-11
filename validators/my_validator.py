# django core
from django.core.exceptions import ValidationError


# Create your validators here


contents_variants = ('z przeniesienia', 'Z przeniesienia', 'Z Przeniesienia', 'Z PRZENIESIENIA', 'z Przeniesienia')

def check_pesel(digit:str):
    if len(digit) != 11:
        raise ValidationError('Pesel need to eleven digits...', code='invalid')


def positive_value(value):
    if value < 0:
        raise ValidationError('The value %(value)s must be greater than or equal to zero...', code='invalid')


def from_transfer(contents:str):
    if contents in contents_variants:
        raise  ValidationError('%(contenst)s is not allowed! Use any other...', code='invalid', params={'contents': contents})
