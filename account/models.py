# django core
from django.db import models
from django.conf import settings

# Create your models here.


class Quiz(models.Model):
	player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
	set_of_questions = models.PositiveIntegerField(null=True,)
	query = models.CharField(max_length=250, null=True)
	answer = models.CharField(max_length=250, null=True)
	answers = models.TextField(null=True,)
	start_play = models.DateTimeField(null=True,)
	end_play = models.DateTimeField(null=True,)
	points = models.SmallIntegerField(null=True,)


class CreationModificationDateMixin(models.Model):
	""" Abstract base class with a creation and modification date and time"""
	class Meta:
		abstract = True
		
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
