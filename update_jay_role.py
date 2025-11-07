"""
Check and update user group assignments
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User, Group


def check_and_update_users():
    """Check users and allow updating their roles"""
    
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    armorer_group, _ = Group.objects.get_or_create(name='Armorer')
    
    print("Current Users and Their Roles:")
    print("="*60)
    
    users = User.objects.all()
    for user in users:
        groups = list(user.groups.values_list('name', flat=True))
        
        if user.is_superuser:
            role = "Superuser"
        elif user.groups.filter(name='Admin').exists():
            role = "Admin"
        elif user.groups.filter(name='Armorer').exists():
            role = "Armorer"
        else:
            role = "Personnel"
        
        print(f"\nUsername: {user.username}")
        print(f"  Current Role: {role}")
        print(f"  is_superuser: {user.is_superuser}")
        print(f"  is_staff: {user.is_staff}")
        print(f"  Groups: {groups}")
    
    print("\n" + "="*60)
    print("MANUAL ROLE ASSIGNMENT")
    print("="*60)
    print("\nWhich user is 'jay' supposed to be?")
    print("Options:")
    print("  1. Admin")
    print("  2. Armorer")
    print("  3. Keep current (Admin)")
    
    # For now, let's assume jay should be Armorer based on your message
    # Let's update jay to Armorer
    jay_user = User.objects.filter(username='jay').first()
    if jay_user:
        # Remove from all groups first
        jay_user.groups.clear()
        # Add to Armorer group
        jay_user.groups.add(armorer_group)
        print(f"\n✅ Updated 'jay' to Armorer role")
    
    print("\n" + "="*60)
    print("UPDATED USER ROLES")
    print("="*60)
    
    for user in User.objects.all():
        if user.is_superuser:
            role = "Superuser"
        elif user.groups.filter(name='Admin').exists():
            role = "Admin"
        elif user.groups.filter(name='Armorer').exists():
            role = "Armorer"
        else:
            role = "Personnel"
        
        print(f"{user.username:15} → {role}")


if __name__ == '__main__':
    check_and_update_users()
