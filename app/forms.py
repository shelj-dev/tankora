from django import forms
from .models import GasDevice

class GasDeviceForm(forms.ModelForm):
    class Meta:
        model = GasDevice
        fields = [
            'device_id', 'current_level', 'valve_status', 
            'auto_booking_enabled', 'booking_threshold', 
            'user', 'supplier_email', 'alert_email', 
            'full_weight', 'gross_weight', 'current_weight', 'prediction'
        ]
        widgets = {
            'device_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. pico_gas_monitor'}),
            'current_level': forms.NumberInput(attrs={'class': 'form-input'}),
            'valve_status': forms.Select(attrs={'class': 'form-select'}),
            'auto_booking_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'booking_threshold': forms.NumberInput(attrs={'class': 'form-input'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'supplier_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'supply@tankora.com'}),
            'alert_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'security@tankora.com'}),
            'full_weight': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Full'}),
            'gross_weight': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Gross'}),
            'current_weight': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Current'}),
            'prediction': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Prediction'}),
        }
