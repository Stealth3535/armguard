import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pathlib import Path
from django.conf import settings

print("=" * 60)
print("QR CODE FOLDER STRUCTURE CHECK")
print("=" * 60)

media_root = Path(settings.MEDIA_ROOT)
qr_root = media_root / 'qr_codes'

print(f"\nMedia Root: {media_root}")
print(f"QR Root: {qr_root}")

if qr_root.exists():
    print(f"\n✓ QR Codes folder exists")
    
    # Check subfolders
    personnel_dir = qr_root / 'personnel'
    item_dir = qr_root / 'item'
    
    print(f"\nPersonnel folder: {personnel_dir}")
    if personnel_dir.exists():
        files = list(personnel_dir.glob('*.png'))
        print(f"  ✓ Exists - {len(files)} QR codes")
        for f in files[:5]:
            print(f"    - {f.name}")
    else:
        print(f"  ✗ Does not exist")
    
    print(f"\nItem folder: {item_dir}")
    if item_dir.exists():
        files = list(item_dir.glob('*.png'))
        print(f"  ✓ Exists - {len(files)} QR codes")
        for f in files[:5]:
            print(f"    - {f.name}")
    else:
        print(f"  ✗ Does not exist")
    
    # Check for files in root qr_codes folder
    print(f"\nFiles in root qr_codes folder:")
    root_files = [f for f in qr_root.iterdir() if f.is_file()]
    if root_files:
        print(f"  ⚠ WARNING: {len(root_files)} files in root (should be in subfolders)")
        for f in root_files[:5]:
            print(f"    - {f.name}")
    else:
        print(f"  ✓ No files in root (all in subfolders)")
        
else:
    print(f"\n✗ QR Codes folder does not exist yet")

print("\n" + "=" * 60)
print("QR CODE IMAGE MODEL CHECK")
print("=" * 60)

from qr_manager.models import QRCodeImage

personnel_qrs = QRCodeImage.objects.filter(qr_type='personnel')
item_qrs = QRCodeImage.objects.filter(qr_type='item')

print(f"\nPersonnel QR records: {personnel_qrs.count()}")
for qr in personnel_qrs[:3]:
    print(f"  - {qr.reference_id}: {qr.qr_image.name if qr.qr_image else 'No image'}")

print(f"\nItem QR records: {item_qrs.count()}")
for qr in item_qrs[:3]:
    print(f"  - {qr.reference_id}: {qr.qr_image.name if qr.qr_image else 'No image'}")
