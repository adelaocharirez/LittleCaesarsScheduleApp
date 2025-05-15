# littlecaesars/forms.py
from django import forms
from .models import Shift, Availability, Employee
from django.db import models # Add this import

class NameEntryForm(forms.Form):
    full_name = forms.CharField(
        label='Enter Your Full Name',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'First Last'})
    )

class AvailabilitySelectionForm(forms.Form):
    selected_shifts = forms.ModelMultipleChoiceField(
        queryset=Shift.objects.all(), # Start with all shifts, can refine later
        widget=forms.CheckboxSelectMultiple,
        required=False # Validation handled in clean method
    )

    def __init__(self, *args, **kwargs):
        # Get employee passed from the view for context
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        # We'll rely on the template structure to group by day visually.
        # The queryset for the field includes all shifts for selection logic.

    def clean_selected_shifts(self):
        selected_shifts = self.cleaned_data.get('selected_shifts')
        if not selected_shifts: # Handle case where nothing is selected
             raise forms.ValidationError("Please select the shifts you are available for.")

        selected_days = {shift.day_of_week for shift in selected_shifts}

        # Min/Max Day Validation
        if len(selected_days) < 3:
            raise forms.ValidationError("Please select availability for at least 3 different days.")
        if len(selected_days) > 5:
            raise forms.ValidationError("Please select availability for no more than 5 different days.")

        # Capacity Validation
        # Fetch current counts efficiently to minimize DB hits inside loop
        current_counts = {
            item['shift_id']: item['count'] # Corrected: Use dictionary key access
            for item in Availability.objects.filter(shift__in=selected_shifts).values('shift_id').annotate(count=models.Count('id'))
        }
        # Check if employee is already counted for relevant shifts (important if re-submitting)
        already_available_shifts = set(
            Availability.objects.filter(employee=self.employee, shift__in=selected_shifts).values_list('shift_id', flat=True)
        )

        for shift in selected_shifts:
            count = current_counts.get(shift.id, 0)
            # Only check capacity if employee isn't already listed for this shift
            if shift.id not in already_available_shifts:
                if count >= shift.get_max_capacity():
                    raise forms.ValidationError(f"Sorry, the shift '{shift}' is already full ({count}/{shift.get_max_capacity()}).")

        return selected_shifts