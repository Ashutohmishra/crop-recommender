# profiles/forms.py

from django import forms
from .models import FarmerProfile
import re

class FarmerProfileForm(forms.ModelForm):
    current_crops = forms.MultipleChoiceField(
        choices=FarmerProfile.CROP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    help_needed = forms.MultipleChoiceField(
        choices=FarmerProfile.HELP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = FarmerProfile
        fields = [
            'full_name', 'phone', 'country', 'profile_image',
            'pan_number', 'aadhaar_number', 'pm_kisan_registered', 'pm_kisan_id',
            'current_crops', 'land_area', 'land_unit', 'help_needed', 'help_description',
            'address', 'state', 'district', 'village', 'pincode'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'country': forms.Select(attrs={'class': 'form-control', 'id': 'country-select'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABCDE1234F'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12-digit Aadhaar'}),
            'pm_kisan_registered': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pm_kisan_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PM-KISAN ID'}),
            'land_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Land area'}),
            'land_unit': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('acres', 'Acres'),
                ('hectares', 'Hectares'),
                ('bigha', 'Bigha'),
                ('guntha', 'Guntha'),
            ]),
            'help_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your needs...'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'village': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village/Town'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN/ZIP Code'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone = re.sub(r'[^\d+]', '', phone)
        
        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits. Please enter a valid number.")
        
        if len(phone) > 15:
            raise forms.ValidationError("Phone number is too long. Please enter a valid number.")
        
        return phone

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number')
        country = self.cleaned_data.get('country')
        
        if country == 'india' and pan:
            pan = pan.upper().strip()
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
                raise forms.ValidationError("Invalid PAN format. It should be like ABCDE1234F")
            return pan
        return pan

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        country = self.cleaned_data.get('country')
        
        if country == 'india' and aadhaar:
            aadhaar = re.sub(r'\D', '', aadhaar)
            if len(aadhaar) != 12:
                raise forms.ValidationError("Aadhaar number must be exactly 12 digits.")
            return aadhaar
        return aadhaar

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get('country')
        
        if country != 'india':
            cleaned_data['pan_number'] = None
            cleaned_data['aadhaar_number'] = None
            cleaned_data['pm_kisan_registered'] = False
            cleaned_data['pm_kisan_id'] = None
        
        return cleaned_data


class PhoneVerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control verification-input',
            'placeholder': 'Enter 6-digit code',
            'maxlength': '6',
            'pattern': '[0-9]{6}'
        })
    )
