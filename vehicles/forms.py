from django import forms
from .models import Inspection, Vehicle


class InspectionForm(forms.ModelForm):
    """
    Unified form for both simple and detailed modes.
    User can either pick a Vehicle from the dropdown OR type their own
    vehicle name in `custom_vehicle`. For detailed mode, brand/model/year etc.
    are filled in as well.
    """
    mode = forms.ChoiceField(
        choices=Inspection.MODE_CHOICES,
        widget=forms.HiddenInput(),
        initial='simple',
    )

    class Meta:
        model = Inspection
        fields = [
            'mode', 'vehicle', 'custom_vehicle', 'image',
            'brand', 'model_name', 'year', 'color',
            'mileage', 'fuel_type', 'transmission', 'additional_info',
        ]

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.all()
        self.fields['vehicle'].required = False
        self.fields['vehicle'].empty_label = '—'
        # Make all detailed fields optional at the form layer
        for name in ['custom_vehicle', 'brand', 'model_name', 'year', 'color',
                     'mileage', 'fuel_type', 'transmission', 'additional_info']:
            self.fields[name].required = False
        self.fields['image'].required = True

        # Attach human-readable labels for templates that loop fields
        self.fields['vehicle'].label = 'Vehicle'
        self.fields['image'].label = 'Photo'

    def clean(self):
        cleaned = super().clean()
        # Require either picked vehicle OR custom typed vehicle
        if not cleaned.get('vehicle') and not (cleaned.get('custom_vehicle') or '').strip():
            raise forms.ValidationError(
                "Please pick a vehicle from the list or type your vehicle's name."
            )
        return cleaned
