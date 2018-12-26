# django core
from django.core.exceptions import ValidationError

# standard library
from datetime import datetime

def check_pesel(digit:str):
    if len(digit) != 11:
        raise ValidationError(('Pesel need to eleven digits'),)
