# django core
from django.core.exceptions import ValidationError


# Create your validators here


contenst_variants = ('z przeniesienia', 'Z przeniesienia',
					 'Z Przeniesienia', 'Z PRZENIESIENIA',
					 'z Przeniesienia', 'z PRZENIESIENIA')

def check_pesel(digit:str):
	if len(digit) != 11:
		raise ValidationError('Pesel need to eleven digits...', params={'digit': digit},)


def positive_value(value):
	if isinstance(value, float):
		if value < 0:
			raise ValidationError('The value %(value)s must be greater than or equal to zero...', params={'value': value},)


def from_transfer(contenst:str):
	if contenst in contenst_variants:
		raise  ValidationError('%(contenst)s is not allowed! Use any other...', params={'contenst': contenst},)
