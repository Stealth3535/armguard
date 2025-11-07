from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count
from django.conf import settings
from inventory.models import Item
from personnel.models import Personnel
from transactions.models import Transaction
from .forms import (
    UserRegistrationForm, AdminUserForm, ArmorerRegistrationForm, 
    PersonnelRegistrationForm, ItemRegistrationForm
)
from utils.qr_generator import generate_qr_code
from pathlib import Path
import os


def is_admin_user(user):
    """Check if user is staff but not necessarily superuser"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Custom admin dashboard for non-superuser admins"""
    # Get statistics
    total_items = Item.objects.count()
    total_personnel = Personnel.objects.count()
    total_transactions = Transaction.objects.count()
    total_users = User.objects.count()
    
    # Recent transactions
    recent_transactions = Transaction.objects.select_related('personnel', 'item').order_by('-date_time')[:10]
    
    # Items by type
    items_by_type = Item.objects.values('item_type').annotate(count=Count('id'))
    
    context = {
        'total_items': total_items,
        'total_personnel': total_personnel,
        'total_transactions': total_transactions,
        'total_users': total_users,
        'recent_transactions': recent_transactions,
        'items_by_type': items_by_type,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_management(request):
    """User management page for admins"""
    users = User.objects.all().order_by('-date_joined')
    personnel = Personnel.objects.all().order_by('surname', 'firstname')
    
    context = {
        'users': users,
        'personnel': personnel,
    }
    return render(request, 'admin/user_management.html', context)


@login_required
@user_passes_test(is_admin_user)
def create_user(request):
    """Create new user with personnel profile (admin/armorer/personnel)"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        
        # Get role first to determine validation
        role = request.POST.get('role', '')
        
        # For personnel, username, email and password are optional
        if role == 'personnel':
            # Remove validation errors for username, email and password for personnel
            if form.errors.get('username'):
                del form.errors['username']
            if form.errors.get('email'):
                del form.errors['email']
            if form.errors.get('password'):
                del form.errors['password']
            if form.errors.get('confirm_password'):
                del form.errors['confirm_password']
        
        if form.is_valid() or (role == 'personnel' and 'surname' in request.POST):
            username = form.cleaned_data.get('username', '') or request.POST.get('username', '')
            email = form.cleaned_data.get('email', '')
            password = form.cleaned_data.get('password', '')
            
            # Personnel fields
            surname = form.cleaned_data.get('surname') or request.POST.get('surname')
            firstname = form.cleaned_data.get('firstname') or request.POST.get('firstname')
            middle_initial = form.cleaned_data.get('middle_initial', '') or request.POST.get('middle_initial', '')
            rank = form.cleaned_data.get('rank') or request.POST.get('rank')
            serial = form.cleaned_data.get('serial') or request.POST.get('serial')
            office = form.cleaned_data.get('office') or request.POST.get('office')
            tel = form.cleaned_data.get('tel') or request.POST.get('tel')
            picture = request.FILES.get('picture')
            
            # Check if personnel serial exists
            if Personnel.objects.filter(serial=serial).exists():
                messages.error(request, 'Personnel with this serial number already exists.')
                return redirect('custom_admin:create_user')
            
            # Determine if officer based on rank
            is_officer = rank in [r[0] for r in Personnel.RANKS_OFFICER]
            
            # Apply capitalization based on officer/enlisted status
            if is_officer:
                # Officers: UPPERCASE for surname and firstname
                surname = surname.upper()
                firstname = firstname.upper()
                if middle_initial:
                    middle_initial = middle_initial.upper()
            else:
                # Enlisted: Title case for surname and firstname
                surname = surname.title()
                firstname = firstname.title()
                if middle_initial:
                    middle_initial = middle_initial.upper()
            
            # Rank is always uppercase
            rank = rank.upper()
            
            # Create Personnel record
            personnel = Personnel(
                surname=surname,
                firstname=firstname,
                middle_initial=middle_initial,
                rank=rank,
                serial=serial,
                office=office,
                tel=tel,
                picture=picture
            )
            personnel.save()
            # QR code will be automatically generated by signal
            
            # Create User account only for admin and armorer
            if role in ['admin', 'armorer']:
                # Check if username exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, f'Username "{username}" already exists.')
                    personnel.delete()  # Rollback personnel creation
                    return redirect('custom_admin:create_user')
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Set permissions based on role
                if role == 'admin':
                    user.is_staff = True
                    user.is_superuser = False
                    # Add to Admin group
                    admin_group, _ = Group.objects.get_or_create(name='Admin')
                    user.groups.add(admin_group)
                elif role == 'armorer':
                    user.is_staff = True
                    user.is_superuser = False
                    # Add to Armorer group
                    armorer_group, _ = Group.objects.get_or_create(name='Armorer')
                    user.groups.add(armorer_group)
                
                user.save()
                
                # Link personnel to user
                personnel.user = user
                personnel.save()
                
                messages.success(request, f'{role.capitalize()} user "{username}" and personnel profile created successfully!')
            else:
                # Personnel only - no user account
                messages.success(request, f'Personnel "{personnel.get_full_name()}" registered successfully (no login account created)!')
            
            return redirect('custom_admin:user_management')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'admin/create_user.html', {'form': form})


@login_required
@user_passes_test(is_admin_user)
def edit_user(request, user_id):
    """Edit user and associated personnel profile using the same registration form"""
    edit_user_obj = get_object_or_404(User, id=user_id)
    
    # Get associated personnel record using the new relationship
    personnel = None
    try:
        personnel = edit_user_obj.personnel
    except Personnel.DoesNotExist:
        # Try to find personnel by serial matching username or by name/last name
        personnel = Personnel.objects.filter(serial=edit_user_obj.username).first()
        if not personnel:
            # Try to find by surname/firstname combination
            # This helps find existing personnel created separately
            all_personnel = Personnel.objects.filter(user__isnull=True)
            # We'll show these in the form dropdown for manual linking
        
        if personnel and not personnel.user:
            # Auto-link this personnel to the user
            personnel.user = edit_user_obj
            personnel.save()
    
    if request.method == 'POST':
        # Prevent non-superusers from editing superusers
        if edit_user_obj.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Only superusers can edit other superusers.')
            return redirect('custom_admin:user_management')
        
        form = UserRegistrationForm(request.POST, request.FILES)
        
        # For existing users, password is optional
        if 'password' in form.errors and not request.POST.get('password'):
            del form.errors['password']
        if 'confirm_password' in form.errors and not request.POST.get('confirm_password'):
            del form.errors['confirm_password']
        
        if form.is_valid() or 'surname' in request.POST:
            # Check if user wants to link to existing personnel
            existing_personnel_id = request.POST.get('existing_personnel')
            
            # Update user account info
            username = form.cleaned_data.get('username') or request.POST.get('username')
            email = form.cleaned_data.get('email', '') or request.POST.get('email', '')
            
            # Check if username is changing and already exists
            if username != edit_user_obj.username and User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists.')
                return redirect('custom_admin:edit_user', user_id=user_id)
            
            edit_user_obj.username = username
            edit_user_obj.email = email
            
            # Update password if provided
            new_password = form.cleaned_data.get('password') or request.POST.get('password', '')
            if new_password:
                edit_user_obj.set_password(new_password)
            
            edit_user_obj.save()
            
            # If user selected existing personnel to link
            if existing_personnel_id:
                try:
                    new_personnel = Personnel.objects.get(id=existing_personnel_id)
                    # Unlink old personnel if exists
                    if personnel and personnel != new_personnel:
                        personnel.user = None
                        personnel.save()
                    # Link new personnel
                    new_personnel.user = edit_user_obj
                    new_personnel.save()
                    personnel = new_personnel
                    messages.success(request, f'User "{edit_user_obj.username}" linked to personnel {personnel.get_full_name()}!')
                except Personnel.DoesNotExist:
                    messages.error(request, 'Selected personnel not found.')
                    return redirect('custom_admin:edit_user', user_id=user_id)
            
            # Update personnel profile if exists
            if personnel:
                surname = form.cleaned_data.get('surname') or request.POST.get('surname')
                firstname = form.cleaned_data.get('firstname') or request.POST.get('firstname')
                middle_initial = form.cleaned_data.get('middle_initial', '') or request.POST.get('middle_initial', '')
                rank = form.cleaned_data.get('rank') or request.POST.get('rank')
                serial = form.cleaned_data.get('serial') or request.POST.get('serial')
                office = form.cleaned_data.get('office') or request.POST.get('office')
                tel = form.cleaned_data.get('tel') or request.POST.get('tel')
                picture = request.FILES.get('picture')
                
                # Check if serial is changing and already exists
                if serial != personnel.serial and Personnel.objects.filter(serial=serial).exists():
                    messages.error(request, 'Personnel with this serial number already exists.')
                    return redirect('custom_admin:edit_user', user_id=user_id)
                
                # Apply capitalization based on officer/enlisted status
                is_officer = rank in [r[0] for r in Personnel.RANKS_OFFICER]
                
                if is_officer:
                    surname = surname.upper()
                    firstname = firstname.upper()
                    if middle_initial:
                        middle_initial = middle_initial.upper()
                else:
                    surname = surname.title()
                    firstname = firstname.title()
                    if middle_initial:
                        middle_initial = middle_initial.upper()
                
                rank = rank.upper()
                
                # Update personnel fields
                personnel.surname = surname
                personnel.firstname = firstname
                personnel.middle_initial = middle_initial
                personnel.rank = rank
                personnel.serial = serial
                personnel.office = office
                personnel.tel = tel
                if picture:
                    personnel.picture = picture
                
                personnel.save()
            
            messages.success(request, f'User "{edit_user_obj.username}" and personnel profile updated successfully.')
            return redirect('custom_admin:user_management')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-fill form with existing data
        initial_data = {
            'username': edit_user_obj.username,
            'email': edit_user_obj.email,
        }
        
        # Determine role
        if edit_user_obj.is_superuser:
            role = 'admin'
        elif edit_user_obj.is_staff:
            role = 'armorer'
        else:
            role = 'personnel'
        
        initial_data['role'] = role
        
        # Add personnel data if exists
        if personnel:
            initial_data.update({
                'surname': personnel.surname,
                'firstname': personnel.firstname,
                'middle_initial': personnel.middle_initial,
                'rank': personnel.rank,
                'serial': personnel.serial,
                'office': personnel.office,
                'tel': personnel.tel,
            })
            # Debug: print to console
            print(f"DEBUG: Editing user {edit_user_obj.username}")
            print(f"DEBUG: Personnel found: {personnel.id}")
            print(f"DEBUG: Initial data: {initial_data}")
        else:
            print(f"DEBUG: No personnel found for user {edit_user_obj.username}")
        
        form = UserRegistrationForm(initial=initial_data, current_personnel=personnel)
    
    context = {
        'form': form,
        'edit_user': edit_user_obj,
        'personnel': personnel,
        'is_edit': True,
    }
    return render(request, 'admin/create_user.html', context)


@login_required
@user_passes_test(is_admin_user)
def edit_personnel(request, personnel_id):
    """Edit personnel profile directly (for personnel with or without user accounts)"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    
    if request.method == 'POST':
        # Get form data
        surname = request.POST.get('surname')
        firstname = request.POST.get('firstname')
        middle_initial = request.POST.get('middle_initial', '')
        rank = request.POST.get('rank')
        serial = request.POST.get('serial')
        office = request.POST.get('office')
        tel = request.POST.get('tel')
        picture = request.FILES.get('picture')
        
        # Check if serial is changing and already exists
        if serial != personnel.serial and Personnel.objects.filter(serial=serial).exists():
            messages.error(request, 'Personnel with this serial number already exists.')
            return redirect('custom_admin:edit_personnel', personnel_id=personnel_id)
        
        # Apply capitalization based on officer/enlisted status
        is_officer = rank in [r[0] for r in Personnel.RANKS_OFFICER]
        
        if is_officer:
            surname = surname.upper()
            firstname = firstname.upper()
            if middle_initial:
                middle_initial = middle_initial.upper()
        else:
            surname = surname.title()
            firstname = firstname.title()
            if middle_initial:
                middle_initial = middle_initial.upper()
        
        rank = rank.upper()
        
        # Update personnel fields
        personnel.surname = surname
        personnel.firstname = firstname
        personnel.middle_initial = middle_initial
        personnel.rank = rank
        personnel.serial = serial
        personnel.office = office
        personnel.tel = tel
        if picture:
            personnel.picture = picture
        
        personnel.save()
        
        messages.success(request, f'Personnel "{personnel.get_full_name()}" updated successfully.')
        return redirect('custom_admin:user_management')
    else:
        # Pre-fill form with existing personnel data
        initial_data = {
            'surname': personnel.surname,
            'firstname': personnel.firstname,
            'middle_initial': personnel.middle_initial,
            'rank': personnel.rank,
            'serial': personnel.serial,
            'office': personnel.office,
            'tel': personnel.tel,
            'role': 'personnel',  # Default to personnel role for display
        }
        
        # If personnel has a user account, include user data
        if personnel.user:
            initial_data.update({
                'username': personnel.user.username,
                'email': personnel.user.email,
            })
            # Determine actual role
            if personnel.user.is_superuser:
                initial_data['role'] = 'admin'
            elif personnel.user.is_staff:
                initial_data['role'] = 'armorer'
        
        form = UserRegistrationForm(initial=initial_data, current_personnel=personnel)
    
    context = {
        'form': form,
        'personnel': personnel,
        'edit_user': personnel.user if personnel.user else None,
        'is_edit': True,
        'is_personnel_edit': True,
    }
    return render(request, 'admin/create_user.html', context)


from django.http import HttpResponseForbidden

@login_required
@user_passes_test(is_admin_user)
def delete_user(request, user_id):
    """Delete user (superuser only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete users.')
        return redirect('custom_admin:user_management')

    user = get_object_or_404(User, id=user_id)
    # Prevent users from deleting themselves
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('custom_admin:user_management')

    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted successfully.')
    return redirect('custom_admin:user_management')


@login_required
@user_passes_test(is_admin_user)
def system_settings(request):
    """System settings page for admins"""
    context = {
        'debug_mode': settings.DEBUG,
    }
    return render(request, 'admin/system_settings.html', context)


@login_required
@user_passes_test(is_admin_user)
def register_item(request):
    """Register new inventory item"""
    if request.method == 'POST':
        form = ItemRegistrationForm(request.POST)
        if form.is_valid():
            item = form.save()
            # QR code will be automatically generated by signal
            
            messages.success(request, f'Item "{item.item_type} - {item.serial}" registered successfully.')
            return redirect('custom_admin:dashboard')
    else:
        form = ItemRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/register_item.html', context)
