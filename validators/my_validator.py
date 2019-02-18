# django core
from django.core.exceptions import ValidationError

def check_pesel(digit:str):
    if len(digit) != 11:
        raise ValidationError(('Pesel need to eleven digits...'),)


def positive_value(value:float):
    if value < 0:
        raise ValidationError(('The value must be greater than or equal to zero...'))
