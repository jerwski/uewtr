# django core
from django.core.exceptions import ValidationError

def check_pesel(digit:str):
    if len(digit) != 11:
        raise ValidationError(('Pesel need to eleven digits'),)
