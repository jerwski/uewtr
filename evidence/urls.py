# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from evidence import views

# Create your Uniform Resource Locator here.

app_name = 'evidence'

urlpatterns = [
    path('time/recorder/employee=<int:employee_id>/', login_required(views.WorkingTimeRecorderView.as_view()), name='working_time_recorder_add'),
    path('time/recorder/employee=<int:employee_id>/end_work_hour=<int:work_hours>/', login_required(views.WorkingTimeRecorderView.as_view()), name='working_time_recorder_add'),
    path('time/recorder/erase/employee=<int:employee_id>/start_work_hour=<str:start_work>/end_work_hour=<str:end_work>/', login_required(views.WorkingTimeRecorderEraseView.as_view()), name='working_time_recorder_erase'),
    path('leave/recorder/employee=<int:employee_id>/', login_required(views.LeaveTimeRecorderView.as_view()), name='leave_time_recorder_add'),
    path('leave/recorder/erase/employee=<int:employee_id>/leave_date=<str:leave_date>/', login_required(views.LeaveTimeRecorderEraseView.as_view()), name='leave_time_recorder_erase'),
    path('monthly/payroll/', login_required(views.MonthlyPayrollView.as_view()), name='monthly_payroll_view'),
    path('account/payment/employee=<int:employee_id>/', login_required(views.AccountPaymentView.as_view()), name='account_payment'),
    path('account/payment/erase/employee=<int:employee_id>/account_date=<str:account_date>/account_value=<str:account_value>/', login_required(views.AccountPaymentEraseView.as_view()), name='account_recorder_erase'),
    path('monthly/payroll/print/month=<int:month>/year=<int:year>/', login_required(views.MonthlyPayrollPrintView.as_view()),name='monthly_payroll_print'),
    path('monthly/payroll/pdf/send/month=<int:month>/year=<int:year>/', login_required(views.SendMonthlyPayrollPdf.as_view()), name='monthly_payroll_pdf'),
    path('leaves_data/print/employee=<int:employee_id>/', login_required(views.LeavesDataPrintView.as_view()),name='leaves_data_print'),
    path('leaves_data/pdf/send/employee=<int:employee_id>/', login_required(views.SendLeavesDataPdf.as_view()), name='leaves_data_pdf'),
    path('complex/data/employee=<int:employee_id>/', login_required(views.EmployeeCurrentComplexDataView.as_view()), name='employee_complex_data'),
    path('chart/employee=<int:employee_id>/', login_required(views.PlotChart.as_view()), name='plot_chart'),
	path('workhours/print/employee=<int:employee_id>/month=<int:month>/year=<int:year>/', login_required(views.WorkhoursPrintView.as_view()),name='workhours_print'),
]
