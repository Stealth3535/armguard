"""
Fix QR Code paths and regenerate QR codes
This script updates QRCodeImage records to use correct paths (items instead of item)
and regenerates all QR code files
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from qr_manager.models import QRCodeImage
from personnel.models import Personnel
from inventory.models import Item
from django.conf import settings
from pathlib import Path
import qrcode
from PIL import Image


def regenerate_all_qr_codes():
    """Delete all QRCodeImage records and regenerate them via signals"""
    print("Deleting old QRCodeImage records...")
    count = QRCodeImage.objects.count()
    QRCodeImage.objects.all().delete()
    print(f"Deleted {count} old records")
    
    # Clean up old QR code files
    qr_codes_dir = Path(settings.MEDIA_ROOT) / 'qr_codes'
    if qr_codes_dir.exists():
        print("\nCleaning old QR code files...")
        for subdir in ['items', 'personnel']:
            subdir_path = qr_codes_dir / subdir
            if subdir_path.exists():
                for file in subdir_path.glob('*.png'):
                    print(f"  Removing: {file.name}")
                    file.unlink()
    
    # Regenerate for all personnel
    print("\nRegenerating personnel QR codes...")
    for person in Personnel.objects.all():
        # Just save to trigger the signal
        person.save()
        print(f"  ✓ Generated QR for {person.get_full_name()} ({person.serial})")
    
    # Regenerate for all items
    print("\nRegenerating item QR codes...")
    for item in Item.objects.all():
        # Just save to trigger the signal
        item.save()
        print(f"  ✓ Generated QR for {item.item_type} ({item.serial})")
    
    # Verify the new paths
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    print(f"\nTotal QRCodeImage records: {QRCodeImage.objects.count()}")
    print("\nQR Code paths in database:")
    for qr in QRCodeImage.objects.all():
        print(f"  - {qr.qr_image}")
    
    # Check file system
    print("\nQR Code files on disk:")
    items_dir = qr_codes_dir / 'items'
    personnel_dir = qr_codes_dir / 'personnel'
    
    if items_dir.exists():
        item_files = list(items_dir.glob('*.png'))
        print(f"\n  Items ({len(item_files)}):")
        for file in item_files:
            print(f"    - {file.name}")
    
    if personnel_dir.exists():
        personnel_files = list(personnel_dir.glob('*.png'))
        print(f"\n  Personnel ({len(personnel_files)}):")
        for file in personnel_files:
            print(f"    - {file.name}")
    
    print("\n✅ QR code regeneration complete!")


if __name__ == '__main__':
    regenerate_all_qr_codes()
