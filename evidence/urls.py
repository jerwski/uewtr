# django core
from django.urls import path

# my views
from evidence import views

app_name = 'evidence'

urlpatterns = [
    path('time/recorder/<int:employee_id>/', views.WorkingTimeRecorderView.as_view(), name='working_time_recorder_add'),
    path('time/recorder/<int:employee_id>/<int:default_work>/', views.WorkingTimeRecorderView.as_view(), name='working_time_recorder_add'),
    path('time/recorder/erase/<int:employee_id>/<str:start_work>/<str:end_work>/', views.WorkingTimeRecorderEraseView.as_view(), name='working_time_recorder_erase'),
    path('leave/recorder/<int:employee_id>/', views.LeaveTimeRecorderView.as_view(), name='leave_time_recorder_add'),
    path('leave/recorder/erase/<int:employee_id>/<str:leave_date>/', views.LeaveTimeRecorderEraseView.as_view(), name='leave_time_recorder_erase'),
    path('monthly/payroll/', views.MonthlyPayrollView.as_view(), name='monthly_payroll_view'),
    path('account/payment/<int:employee_id>/', views.AccountPaymentView.as_view(), name='account_payment'),
    path('account/payment/erase/<int:employee_id>/<str:account_date>/<str:account_value>/', views.AccountPaymentEraseView.as_view(), name='account_recorder_erase'),
    path('monthly/payroll/print/<int:month>/<int:year>/', views.MonthlyPayrollPrintView.as_view(),name='monthly_payroll_print'),
    path('monthly/payroll/pdf/send/<int:month>/<int:year>/', views.SendPayrollPdf.as_view(), name='monthly_payroll_pdf'),
    path('leaves_data/print/<int:employee_id>/', views.LeavesDataPrintView.as_view(),name='leaves_data_print'),
    path('leaves_data/pdf/send/<int:employee_id>/', views.LeavesDataPdf.as_view(),name='leaves_data_pdf'),
    path('complex/data/<int:employee_id>/', views.EmployeeCurrentComplexDataView.as_view(), name='employee_complex_data'),
    path('chart/<int:employee_id>/', views.PlotChart.as_view(), name='plot_chart')
]
