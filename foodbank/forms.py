from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Region, FoodBank, GroceryStore, FoodDonation,
    FoodCategory, DeliveryRoute
)


class RegionSetupForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name', 'center_latitude', 'center_longitude', 'radius_miles', 'truck_capacity_pounds']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Metro Atlanta Food Hub'
            }),
            'center_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '33.7490',
                'step': '0.000001'
            }),
            'center_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '-84.3880',
                'step': '0.000001'
            }),
            'radius_miles': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 35,
                'min': 1,
                'max': 100
            }),
            'truck_capacity_pounds': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 2000,
                'min': 500,
                'max': 10000
            }),
        }


class FoodBankRegistrationForm(forms.ModelForm):
    class Meta:
        model = FoodBank
        fields = [
            'name', 'contact_person', 'email', 'phone', 'address',
            'latitude', 'longitude', 'daily_average_need_pounds',
            'storage_capacity_pounds', 'can_self_pickup',
            'open_time', 'close_time', 'operating_days'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Food Bank Name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary Contact Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@foodbank.org'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete address with zip code'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Latitude (auto-filled from address)'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Longitude (auto-filled from address)'
            }),
            'daily_average_need_pounds': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Average daily food need in pounds',
                'min': 1
            }),
            'storage_capacity_pounds': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum storage capacity in pounds',
                'min': 1
            }),
            'can_self_pickup': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'open_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'close_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'operating_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mon-Fri, Mon-Sat'
            }),
        }


class GroceryStoreRegistrationForm(forms.ModelForm):
    class Meta:
        model = GroceryStore
        fields = [
            'name', 'contact_person', 'email', 'phone', 'address',
            'latitude', 'longitude', 'preferred_pickup_time_start',
            'preferred_pickup_time_end', 'pickup_days'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Store Name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Manager/Contact Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'store@grocery.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete address with zip code'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Latitude (auto-filled from address)'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Longitude (auto-filled from address)'
            }),
            'preferred_pickup_time_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'value': '08:00'
            }),
            'preferred_pickup_time_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'value': '12:00'
            }),
            'pickup_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mon-Fri, Daily',
                'value': 'Mon-Fri'
            }),
        }


class FoodDonationForm(forms.ModelForm):
    class Meta:
        model = FoodDonation
        fields = [
            'category', 'description', 'quantity_pounds',
            'expiration_date', 'sell_by_date'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the food items (e.g., Mixed fresh vegetables, day-old bread, deli meat approaching sell-by date)',
                'required': True
            }),
            'quantity_pounds': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Weight in pounds',
                'step': '0.1',
                'min': '0.1',
                'required': True
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Select expiration date (if applicable)'
            }),
            'sell_by_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Select sell-by date (if applicable)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = FoodCategory.objects.all()
        self.fields['expiration_date'].required = False
        self.fields['sell_by_date'].required = False


class MobileFoodDonationForm(forms.ModelForm):
    """Simplified mobile-optimized version of the food donation form"""

    class Meta:
        model = FoodDonation
        fields = ['category', 'description', 'quantity_pounds', 'expiration_date']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'style': 'font-size: 18px; padding: 15px;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 4,
                'style': 'font-size: 16px; padding: 15px;',
                'placeholder': 'What food items are you donating?'
            }),
            'quantity_pounds': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'style': 'font-size: 18px; padding: 15px;',
                'placeholder': 'Weight (lbs)',
                'step': '0.1',
                'min': '0.1'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'style': 'font-size: 16px; padding: 15px;'
            }),
        }


class RouteConfirmationForm(forms.Form):
    confirm_pickup = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    confirm_delivery = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    alternative_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special instructions or concerns?'
        })
    )


class DriverTeamAssignmentForm(forms.ModelForm):
    class Meta:
        model = DeliveryRoute
        fields = ['driver_team', 'truck_identifier', 'scheduled_date', 'start_time']
        widgets = {
            'driver_team': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Driver 1 & Driver 2 Names'
            }),
            'truck_identifier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Truck ID or License Plate'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'value': '08:00'
            }),
        }


class EmailDonationProcessingForm(forms.Form):
    """Form for manually processing email donations"""

    email_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste the email content here for AI processing...'
        })
    )
    grocery_store = forms.ModelChoiceField(
        queryset=GroceryStore.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        region = kwargs.pop('region', None)
        super().__init__(*args, **kwargs)
        if region:
            self.fields['grocery_store'].queryset = region.grocery_stores.filter(is_active=True)