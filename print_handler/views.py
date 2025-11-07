"""
Print Handler Views
Handles printing of QR codes and transaction forms
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from qr_manager.models import QRCodeImage
from transactions.models import Transaction
from personnel.models import Personnel
from inventory.models import Item
from .pdf_filler.qr_print_layout import get_layout_config, generate_qr_print_pdf
import os
from django.conf import settings
from reportlab.lib.pagesizes import A4, letter


@login_required
def print_qr_codes(request):
    """View for printing QR codes using Python layout configuration"""
    # Check if filtering by type
    qr_type = request.GET.get('type', 'all')
    
    personnel_qrcodes = QRCodeImage.objects.filter(qr_type='personnel') if qr_type in ['all', 'personnel'] else QRCodeImage.objects.none()
    item_qrcodes = QRCodeImage.objects.filter(qr_type='item') if qr_type in ['all', 'items'] else QRCodeImage.objects.none()
    
    # Attach personnel/item details to each QR code
    for qr in personnel_qrcodes:
        try:
            person = Personnel.objects.get(id=qr.reference_id)
            qr.name = person.get_full_name()
            qr.rank = person.rank
        except Personnel.DoesNotExist:
            qr.name = "Unknown"
            qr.rank = ""
    
    for qr in item_qrcodes:
        try:
            item = Item.objects.get(id=qr.reference_id)
            qr.name = f"{item.item_type} - {item.serial}"
            qr.item_type = item.item_type
        except Item.DoesNotExist:
            qr.name = "Unknown"
            qr.item_type = ""
    
    # Get layout configuration from Python file
    layout_config = get_layout_config()
    
    context = {
        'personnel_qrcodes': personnel_qrcodes,
        'item_qrcodes': item_qrcodes,
        'qr_type': qr_type,
        'layout': layout_config,  # Pass Python layout config to template
    }
    return render(request, 'print_handler/print_qr_codes.html', context)


@login_required
def print_single_qr(request, qr_id):
    """Print a single QR code"""
    qr_code = get_object_or_404(QRCodeImage, id=qr_id)
    context = {
        'qr_code': qr_code,
    }
    return render(request, 'print_handler/print_single_qr.html', context)


@login_required
def print_transaction_form(request, transaction_id=None):
    """Print transaction form"""
    transaction = None
    if transaction_id:
        transaction = get_object_or_404(Transaction, id=transaction_id)
    
    context = {
        'transaction': transaction,
    }
    return render(request, 'print_handler/print_transaction_form.html', context)


@login_required
def print_all_transactions(request):
    """Print all transactions or filtered transactions"""
    transactions = Transaction.objects.all().select_related('personnel', 'item').order_by('-date_time')
    
    # Filter by personnel if provided
    personnel_id = request.GET.get('personnel_id')
    if personnel_id:
        transactions = transactions.filter(personnel_id=personnel_id)
    
    # Filter by item if provided
    item_id = request.GET.get('item_id')
    if item_id:
        transactions = transactions.filter(item_id=item_id)
    
    context = {
        'transactions': transactions,
    }
    return render(request, 'print_handler/print_transactions.html', context)


@login_required
def generate_qr_pdf(request):
    """Generate a PDF file with QR codes for printing"""
    # Get filter type
    qr_type = request.GET.get('type', 'all')
    
    # Get QR codes
    personnel_qrcodes = QRCodeImage.objects.filter(qr_type='personnel') if qr_type in ['all', 'personnel'] else QRCodeImage.objects.none()
    item_qrcodes = QRCodeImage.objects.filter(qr_type='item') if qr_type in ['all', 'items'] else QRCodeImage.objects.none()
    
    # Collect QR image paths
    qr_image_paths = []
    
    for qr in personnel_qrcodes:
        if qr.qr_image:
            qr_image_paths.append(qr.qr_image.path)
    
    for qr in item_qrcodes:
        if qr.qr_image:
            qr_image_paths.append(qr.qr_image.path)
    
    if not qr_image_paths:
        return HttpResponse("No QR codes found to print.", status=404)
    
    # Get customization parameters from request (with defaults)
    paper_size_param = request.GET.get('paper', 'A4')
    paper_size = A4 if paper_size_param == 'A4' else letter
    
    qr_size_mm = int(request.GET.get('qr_size', 30))  # Default 30mm (about 1.18 inches)
    margin_mm = int(request.GET.get('margin', 15))     # Default 15mm
    columns = int(request.GET.get('columns', 3))       # Default 3 columns
    rows = int(request.GET.get('rows', 5))             # Default 5 rows
    
    # Generate PDF
    output_filename = f'qr_codes_{qr_type}.pdf'
    output_path = os.path.join(settings.MEDIA_ROOT, 'temp', output_filename)
    
    # Create temp directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    generate_qr_print_pdf(
        qr_images=qr_image_paths,
        output_path=output_path,
        paper_size=paper_size,
        qr_size_mm=qr_size_mm,
        margin_mm=margin_mm,
        columns=columns,
        rows=rows
    )
    
    # Return PDF file
    response = FileResponse(open(output_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{output_filename}"'
    return response


@login_required
def qr_print_settings(request):
    """QR print settings configuration page"""
    return render(request, 'print_handler/qr_print_settings.html')
