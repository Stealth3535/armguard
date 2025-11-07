
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from utils.qr_generator import generate_qr_code
from inventory.models import Item
from personnel.models import Personnel

class Command(BaseCommand):
    help = 'Regenerate missing QR codes for items and personnel based on database records.'

    def handle(self, *args, **options):
        # Items
        media_items_dir = Path(settings.MEDIA_ROOT) / 'qr_codes' / 'items'
        media_items_dir.mkdir(parents=True, exist_ok=True)
        items = Item.objects.all()
        item_count = 0
        for item in items:
            qr_filename = f"{item.qr_code}.png"
            qr_path = media_items_dir / qr_filename
            if not qr_path.exists():
                generate_qr_code(item.qr_code, qr_path)
                self.stdout.write(self.style.SUCCESS(f"Generated QR for item {item.id} (data: {item.qr_code})"))
                item_count += 1

        # Personnel
        media_personnel_dir = Path(settings.MEDIA_ROOT) / 'qr_codes' / 'personnel'
        media_personnel_dir.mkdir(parents=True, exist_ok=True)
        personnel = Personnel.objects.all()
        personnel_count = 0
        for person in personnel:
            qr_filename = f"{person.qr_code}.png"
            qr_path = media_personnel_dir / qr_filename
            if not qr_path.exists():
                generate_qr_code(person.qr_code, qr_path)
                self.stdout.write(self.style.SUCCESS(f"Generated QR for personnel {person.id} (data: {person.qr_code})"))
                personnel_count += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Generated {item_count} item QR codes and {personnel_count} personnel QR codes."))
