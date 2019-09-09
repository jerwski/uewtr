# django core
from django.db import models

class CreationModificationDateMixin(models.Model):
	""" Abstract base class with a creation and modification date and time"""
	class Meta:
		abstract = True

	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
