from django import forms
from .models import Inspection

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = ['vehicle', 'image']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['vehicle'].queryset = user.vehicle_set.all()