# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from employee import views

app_name = 'employee'

urlpatterns = [
    path('add_change/basicdata/', login_required(views.EmployeeBasicDataView.as_view()), name='employee_basicdata'),
    path('add_change/basicdata/<int:employee_id>/', login_required(views.EmployeeBasicDataView.as_view()), name='employee_basicdata'),
    path('add_change/extendeddata/<int:employee_id>/', login_required(views.EmployeeExtendedDataView.as_view()), name='employee_extendeddata'),
    path('add_change/hourly/rate/<int:employee_id>/', login_required(views.EmployeeHourlyRateView.as_view()), name='employee_hourly_rate'),
    path('erase/hourly/rate/<int:employee_id>/', login_required(views.EmployeeHourlyRateEraseView.as_view()), name='employee_hourly_rate_erase'),
    path('erase/all/records/<int:employee_id>/', login_required(views.EmployeeEraseAll.as_view()), name='employee_erase_all_records'),
]
