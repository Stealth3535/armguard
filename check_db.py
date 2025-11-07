import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from personnel.models import Personnel
from inventory.models import Item
from django.contrib.auth.models import User

print("=" * 50)
print("DATABASE CHECK")
print("=" * 50)

print(f"\nPersonnel count: {Personnel.objects.count()}")
print(f"Item count: {Item.objects.count()}")
print(f"User count: {User.objects.count()}")

print("\n" + "=" * 50)
print("RECENT PERSONNEL:")
print("=" * 50)
for p in Personnel.objects.all()[:5]:
    print(f"  ID: {p.id}")
    print(f"  Name: {p.get_full_name()}")
    print(f"  Rank: {p.rank}")
    print(f"  Serial: {p.serial}")
    print(f"  Has User: {p.user is not None}")
    print("-" * 50)

print("\n" + "=" * 50)
print("RECENT ITEMS:")
print("=" * 50)
for i in Item.objects.all()[:5]:
    print(f"  ID: {i.id}")
    print(f"  Type: {i.item_type}")
    print(f"  Serial: {i.serial}")
    print(f"  Status: {i.status}")
    print("-" * 50)

print("\n" + "=" * 50)
print("RECENT USERS:")
print("=" * 50)
for u in User.objects.all()[:5]:
    print(f"  ID: {u.id}")
    print(f"  Username: {u.username}")
    print(f"  Staff: {u.is_staff}")
    print(f"  Superuser: {u.is_superuser}")
    try:
        print(f"  Personnel: {u.personnel.get_full_name()}")
    except:
        print(f"  Personnel: Not linked")
    print("-" * 50)
