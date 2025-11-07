from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from personnel.models import Personnel
from inventory.models import Item
from django.core.validators import RegexValidator


class UserRegistrationForm(forms.Form):
    """Form for registering admin, armorer, or personnel users"""
    # User account fields
    username = forms.CharField(
        max_length=150, 
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'Enter username'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'user@example.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}), 
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}), 
        label='Confirm Password'
    )
    role = forms.ChoiceField(
        choices=[('admin', 'Admin'), ('armorer', 'Armorer'), ('personnel', 'Personnel')], 
        label='Role'
    )
    
    # Link to existing personnel (optional - for editing existing users)
    existing_personnel = forms.ModelChoiceField(
        queryset=Personnel.objects.all(),  # Will be filtered in the view
        required=False,
        label='Link to Existing Personnel',
        help_text='Select an existing personnel record to link (will show: ID - Full Name - Serial)',
        empty_label='-- Keep current or create new --'
    )
    
    def __init__(self, *args, **kwargs):
        current_personnel = kwargs.pop('current_personnel', None)
        super().__init__(*args, **kwargs)
        
        # Filter queryset to show only unlinked personnel (or current one)
        if current_personnel:
            self.fields['existing_personnel'].queryset = Personnel.objects.filter(
                Q(user__isnull=True) | Q(id=current_personnel.id)
            )
        else:
            self.fields['existing_personnel'].queryset = Personnel.objects.filter(user__isnull=True)
    
    
    # Personnel fields
    surname = forms.CharField(
        max_length=100, 
        label='Surname',
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    firstname = forms.CharField(
        max_length=100, 
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    middle_initial = forms.CharField(
        max_length=10, 
        required=False, 
        label='Middle Initial',
        widget=forms.TextInput(attrs={'placeholder': 'M.I.'})
    )
    rank = forms.ChoiceField(
        choices=Personnel.ALL_RANKS,
        label='Rank'
    )
    serial = forms.CharField(
        max_length=20, 
        label='Serial Number', 
        help_text='6 digits for enlisted, or O-XXXXXX for officers',
        widget=forms.TextInput(attrs={'placeholder': '123456 or O-123456'})
    )
    office = forms.ChoiceField(
        choices=Personnel.OFFICE_CHOICES,
        label='Office'
    )
    tel = forms.CharField(
        max_length=13, 
        label='Tel Number', 
        help_text='+639XXXXXXXXX',
        validators=[RegexValidator(r'^\+639\d{9}$', 'Phone must be in format +639XXXXXXXXX')],
        widget=forms.TextInput(attrs={'placeholder': '+639XXXXXXXXX'})
    )
    picture = forms.ImageField(required=False, label='Picture')
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        # Validate serial number format
        serial = cleaned_data.get('serial')
        rank = cleaned_data.get('rank')
        
        if serial and rank:
            # Check if rank is officer
            is_officer = rank in [r[0] for r in Personnel.RANKS_OFFICER]
            
            if is_officer:
                # Officers should have O-XXXXXX format
                if not serial.startswith('O-'):
                    raise forms.ValidationError('Officer serial number must start with "O-" (e.g., O-123456)')
            else:
                # Enlisted should have 6 digits
                if serial.startswith('O-'):
                    raise forms.ValidationError('Enlisted personnel serial number should not start with "O-"')
                if not serial.isdigit():
                    raise forms.ValidationError('Enlisted serial number must be numeric (6 digits)')
                if len(serial) != 6:
                    raise forms.ValidationError('Enlisted serial number must be exactly 6 digits')
        
        return cleaned_data


class AdminUserForm(forms.Form):
    """Form for creating admin users"""
    username = forms.CharField(max_length=150, label='Username')
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name = forms.CharField(max_length=150, required=False, label='Last Name')
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class ArmorerRegistrationForm(forms.Form):
    """Form for creating armorer users"""
    username = forms.CharField(max_length=150, label='Username')
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name = forms.CharField(max_length=150, required=False, label='Last Name')
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class PersonnelRegistrationForm(forms.ModelForm):
    """Form for registering personnel only (no user account)"""
    class Meta:
        model = Personnel
        fields = [
            'surname', 'firstname', 'middle_initial', 'rank', 'serial', 
            'office', 'tel', 'status', 'picture'
        ]
        widgets = {
            'surname': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'firstname': forms.TextInput(attrs={'placeholder': 'First name'}),
            'middle_initial': forms.TextInput(attrs={'placeholder': 'M.I.'}),
            'serial': forms.TextInput(attrs={'placeholder': '123456 or O-123456'}),
            'tel': forms.TextInput(attrs={'placeholder': '+639XXXXXXXXX'}),
        }


class ItemRegistrationForm(forms.ModelForm):
    """Form for registering inventory items"""
    class Meta:
        model = Item
        fields = [
            'item_type', 'serial', 'description', 'condition', 'status'
        ]
        widgets = {
            'serial': forms.TextInput(attrs={'placeholder': 'Serial number'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Item description'}),
        }
