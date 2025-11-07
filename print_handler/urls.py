"""
Print Handler URLs
"""
from django.urls import path
from . import views

app_name = 'print_handler'

urlpatterns = [
    # QR Code Printing
    path('qr-codes/', views.print_qr_codes, name='print_qr_codes'),
    path('qr-codes/<int:qr_id>/', views.print_single_qr, name='print_single_qr'),
    path('qr-codes/pdf/', views.generate_qr_pdf, name='generate_qr_pdf'),  # PDF generation
    path('qr-codes/settings/', views.qr_print_settings, name='qr_print_settings'),  # Print settings page
    
    # Transaction Form Printing
    path('transaction-form/', views.print_transaction_form, name='print_transaction_form'),
    path('transaction-form/<int:transaction_id>/', views.print_transaction_form, name='print_transaction_form_detail'),
    path('transactions/', views.print_all_transactions, name='print_all_transactions'),
]
