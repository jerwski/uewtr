# django core
from django.urls import path

# my views
from employee import views

app_name = 'employee'

urlpatterns = [
    path('add_change/basicdata/', views.EmployeeBasicDataView.as_view(), name='employee_basicdata'),
    path('add_change/basicdata/<int:employee_id>/', views.EmployeeBasicDataView.as_view(), name='employee_basicdata'),
    path(r'add_change/extendeddata/<int:employee_id>/', views.EmployeeExtendedDataView.as_view(), name='employee_extendeddata'),
    path('add_change/hourly/rate/<int:employee_id>/', views.EmployeeHourlyRateView.as_view(), name='employee_hourly_rate'),
    path('erase/hourly/rate/<int:employee_id>/', views.EmployeeHourlyRateEraseView.as_view(), name='employee_hourly_rate_erase'),
]
