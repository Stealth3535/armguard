#!/usr/bin/env python
"""
Quick script to check and manually link users to personnel
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from personnel.models import Personnel

print("=" * 60)
print("USERS IN DATABASE:")
print("=" * 60)
for u in User.objects.all():
    try:
        pers = u.personnel
        print(f"User ID {u.id}: {u.username:15} -> Personnel: {pers.get_full_name()} ({pers.id})")
    except Personnel.DoesNotExist:
        print(f"User ID {u.id}: {u.username:15} -> NO PERSONNEL LINKED")

print("\n" + "=" * 60)
print("PERSONNEL IN DATABASE:")
print("=" * 60)
for p in Personnel.objects.all():
    user_info = f"User: {p.user.username}" if p.user else "NO USER LINKED"
    print(f"Personnel {p.id}: {p.get_full_name():30} Serial: {p.serial:15} {user_info}")

print("\n" + "=" * 60)
print("MANUAL LINKING:")
print("=" * 60)

# Example: Link user ID 3 (jay) to personnel PE-994360041125
# Uncomment and modify these lines to link:

user_id = 3  # User ID from above
personnel_id = "PE-994360041125"  # Personnel ID from above

try:
    user = User.objects.get(id=user_id)
    personnel = Personnel.objects.get(id=personnel_id)
    
    print(f"\nLinking User '{user.username}' to Personnel '{personnel.get_full_name()}'...")
    personnel.user = user
    personnel.save()
    print(f"✓ SUCCESS: Linked!")
    
except User.DoesNotExist:
    print(f"✗ ERROR: User ID {user_id} not found")
except Personnel.DoesNotExist:
    print(f"✗ ERROR: Personnel ID {personnel_id} not found")

print("\n" + "=" * 60)
print("UPDATED LINKS:")
print("=" * 60)
for u in User.objects.all():
    try:
        pers = u.personnel
        print(f"User ID {u.id}: {u.username:15} -> Personnel: {pers.get_full_name()} ({pers.id})")
    except Personnel.DoesNotExist:
        print(f"User ID {u.id}: {u.username:15} -> NO PERSONNEL LINKED")
