"""
QR Code Models for ArmGuard
Handles QR code generation and management using unified qr_generator
"""
from django.db import models
from django.utils import timezone
from django.core.files import File
from utils.qr_generator import generate_qr_code_to_buffer


def qr_upload_path(instance, filename):
    """Dynamic upload path based on QR type"""
    if instance.qr_type == 'item':
        return f'qr_codes/items/{filename}'
    else:
        return f'qr_codes/{instance.qr_type}/{filename}'


class QRCodeImage(models.Model):
    """QR Code storage model"""
    
    # QR Code type
    TYPE_PERSONNEL = 'personnel'
    TYPE_ITEM = 'item'
    
    TYPE_CHOICES = [
        (TYPE_PERSONNEL, 'Personnel'),
        (TYPE_ITEM, 'Item'),
    ]
    
    # Fields
    qr_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reference_id = models.CharField(max_length=100, help_text="Personnel ID or Item ID")
    qr_data = models.CharField(max_length=255, help_text="Data encoded in QR code")
    qr_image = models.ImageField(upload_to=qr_upload_path, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'qr_codes'
        ordering = ['-created_at']
        verbose_name = 'QR Code'
        verbose_name_plural = 'QR Codes'
        unique_together = ['qr_type', 'reference_id']
    
    def __str__(self):
        return f"{self.qr_type} QR: {self.reference_id}"
    
    def generate_qr_code(self, size=300, box_size=10, border=1):
        """Generate QR code image using unified qr_generator - Standard format"""
        # Use unified QR generator for consistency across all systems
        buffer = generate_qr_code_to_buffer(self.qr_data, size=size)
        
        # Save to model - filename is just the reference_id (e.g., IP-854643041125.png)
        filename = f"{self.reference_id}.png"
        self.qr_image.save(filename, File(buffer), save=False)
        
        return self.qr_image
    
    def save(self, *args, **kwargs):
        """Override save to generate QR code if not exists"""
        if not self.qr_image:
            self.generate_qr_code()
        super().save(*args, **kwargs)

