# django core
from django.core.exceptions import ValidationError

# Create your validators here

def check_pesel(digit:str):
    if len(digit) != 11:
        raise ValidationError('Pesel need to eleven digits...', code='invalid')


def positive_value(value:float):
    if int(value) < 0:
        raise ValidationError('The value %(value)s must be greater than or equal to zero...', params={'value': value})


def from_transfer(contents:str):
    variants = ('z przeniesienia', 'Z przeniesienia', 'Z Przeniesienia', 'Z PRZENIESIENIA')
    if contents in variants:
        raise  ValidationError('%(contenst)s is not allowed! Use any other...', params={'contents': contents})
