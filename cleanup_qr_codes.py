import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pathlib import Path
from django.conf import settings
from qr_manager.models import QRCodeImage

print("=" * 60)
print("CLEANING UP QR CODE FILES")
print("=" * 60)

media_root = Path(settings.MEDIA_ROOT)
qr_root = media_root / 'qr_codes'

# Delete old files in root qr_codes folder
print("\n1. Removing old QR files from root folder...")
root_files = [f for f in qr_root.iterdir() if f.is_file() and f.suffix == '.png']
for f in root_files:
    print(f"   Deleting: {f.name}")
    f.unlink()
print(f"   ✓ Removed {len(root_files)} old files")

# Regenerate QR codes for all records
print("\n2. Regenerating QR codes with new path structure...")

personnel_qrs = QRCodeImage.objects.filter(qr_type='personnel')
print(f"\n   Personnel QR codes: {personnel_qrs.count()}")
for qr in personnel_qrs:
    # Delete old image
    if qr.qr_image:
        try:
            qr.qr_image.delete(save=False)
        except:
            pass
    # Regenerate
    qr.qr_image = None
    qr.save()
    print(f"   ✓ Regenerated: {qr.reference_id} -> {qr.qr_image.name}")

item_qrs = QRCodeImage.objects.filter(qr_type='item')
print(f"\n   Item QR codes: {item_qrs.count()}")
for qr in item_qrs:
    # Delete old image
    if qr.qr_image:
        try:
            qr.qr_image.delete(save=False)
        except:
            pass
    # Regenerate
    qr.qr_image = None
    qr.save()
    print(f"   ✓ Regenerated: {qr.reference_id} -> {qr.qr_image.name}")

print("\n" + "=" * 60)
print("CLEANUP COMPLETE!")
print("=" * 60)
print("\nAll QR codes are now organized in subfolders:")
print("  - media/qr_codes/personnel/")
print("  - media/qr_codes/item/")
