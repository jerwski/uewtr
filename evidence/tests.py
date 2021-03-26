# standart library
from datetime import datetime
from collections import namedtuple

# Django library
from django.conf import settings
from django.test import TestCase
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404

# my models
from employee.models import Employee
from evidence.models import WorkEvidence

# Create your tests here


class WorkingHourTests(TestCase):
	def setUp(self):
		settings.USE_TZ = False
		start = [datetime(2018,9,i,6,0) for i in range(1, 31)]
		end = [datetime(2018,9,i,14,0) for i in range(1, 31)]
		# create dictionary from start and end elements
		dataset = zip(start,end)
		employe = Employee.objects.create(forename='Forename', surname='Surname', pesel='73021602009', status=True)
		worker = get_object_or_404(Employee, pk=employe.id)
		# create data in evidence_workevidence table
		for k,v in dataset:
			WorkEvidence.objects.create(worker=worker, start_work=k, end_work=v, jobhours=8)
		settings.USE_TZ = True


	def testAmountWorkhours(self):
		"""method for data compare"""
		expected_hours = (160,40,40,240)

		filters = (Q(worker_id=1, start_work__week_day__gt=1, end_work__week_day__lt=7),
				   Q(worker_id=1, start_work__week_day=7, end_work__week_day=7),
				   Q(worker_id=1, start_work__week_day=1, end_work__week_day=1),
				   Q(worker_id=1))

		# create generator for pair with key as queryset and value as expected sum of hours
		comparison_of_hours=zip([WorkEvidence.objects.filter(q) for q in filters], expected_hours)

		# comparison of data
		print('test_result: ')
		for query, value in comparison_of_hours:
			qs = query.aggregate(amount=Sum('jobhours'))
			self.assertEqual(qs['amount'] == value, True)
			print(f'{qs["amount"]} hours, ', end='')

		# create namedtuple for filters
		expected_results = namedtuple('expected_results', ['week_hours', 'saturday_hours', 'sunday_hours', 'all_hours'])

		print(f'\n{expected_results._make(expected_hours)}')
