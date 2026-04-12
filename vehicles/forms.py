from django import forms
from .models import Inspection, Vehicle


class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = ['vehicle', 'image']

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.all()
        self.fields['vehicle'].label = 'Транспортное средство'
        self.fields['image'].label = 'Фотография'
