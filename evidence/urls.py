# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from evidence import views

app_name = 'evidence'

urlpatterns = [
    path('time/recorder/<int:employee_id>/', login_required(views.WorkingTimeRecorderView.as_view()), name='working_time_recorder_add'),
    path('time/recorder/<int:employee_id>/end_work_hour=<int:work_hours>/', login_required(views.WorkingTimeRecorderView.as_view()), name='working_time_recorder_add'),
    path('time/recorder/erase/<int:employee_id>/<str:start_work>/<str:end_work>/', login_required(views.WorkingTimeRecorderEraseView.as_view()), name='working_time_recorder_erase'),
    path('leave/recorder/<int:employee_id>/', login_required(views.LeaveTimeRecorderView.as_view()), name='leave_time_recorder_add'),
    path('leave/recorder/erase/<int:employee_id>/<str:leave_date>/', login_required(views.LeaveTimeRecorderEraseView.as_view()), name='leave_time_recorder_erase'),
    path('monthly/payroll/', login_required(views.MonthlyPayrollView.as_view()), name='monthly_payroll_view'),
    path('account/payment/<int:employee_id>/', login_required(views.AccountPaymentView.as_view()), name='account_payment'),
    path('account/payment/erase/<int:employee_id>/<str:account_date>/<str:account_value>/', login_required(views.AccountPaymentEraseView.as_view()), name='account_recorder_erase'),
    path('monthly/payroll/print/<int:month>/<int:year>/', login_required(views.MonthlyPayrollPrintView.as_view()),name='monthly_payroll_print'),
    path('monthly/payroll/pdf/send/<int:month>/<int:year>/', login_required(views.SendPayrollPdf.as_view()), name='monthly_payroll_pdf'),
    path('leaves_data/print/<int:employee_id>/', login_required(views.LeavesDataPrintView.as_view()),name='leaves_data_print'),
    path('leaves_data/pdf/send/<int:employee_id>/', login_required(views.LeavesDataPdf.as_view()),name='leaves_data_pdf'),
    path('complex/data/<int:employee_id>/', login_required(views.EmployeeCurrentComplexDataView.as_view()), name='employee_complex_data'),
    path('chart/<int:employee_id>/', login_required(views.PlotChart.as_view()), name='plot_chart'),
]
