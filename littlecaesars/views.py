# littlecaesars/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction, models # Ensure models is imported
from django.contrib import messages
from .forms import NameEntryForm, AvailabilitySelectionForm
from .models import Employee, Shift, Availability


def enter_name_view(request):
    if request.method == 'POST':
        form = NameEntryForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip().title() # Clean up name
            # Use update_or_create to handle existing names cleanly
            employee, created = Employee.objects.update_or_create(
                full_name=full_name # Use a consistent identifier
                # defaults={'any_other_field': value} # Optional: set defaults if needed
            )
            request.session['employee_id'] = employee.id
            request.session['employee_name'] = employee.full_name # Store name for display
            return redirect('littlecaesars:select_availability') # Use app namespace
    else:
        form = NameEntryForm()
    return render(request, 'littlecaesars/enter_name.html', {'form': form})

def select_availability_view(request):
    employee_id = request.session.get('employee_id')
    employee_name = request.session.get('employee_name', 'Guest') # Get name from session

    if not employee_id:
        messages.error(request, "Please enter your name first.")
        return redirect('littlecaesars:enter_name')

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found. Please enter your name again.")
        # Clear potentially invalid session data
        request.session.pop('employee_id', None)
        request.session.pop('employee_name', None)
        return redirect('littlecaesars:enter_name')

    # Prepare data needed for the template regardless of GET/POST
    # Fetch all shifts ordered correctly, prefetch related data
    all_shifts = Shift.objects.prefetch_related('available_employees__employee').order_by('day_of_week', 'time_slot')

    # Get current availability counts and names efficiently
    availability_data = {}
    for shift in all_shifts:
         # Fetch employees available for this specific shift instance
         available_employees = shift.available_employees.all() # Uses prefetched data
         availability_data[shift.id] = {
             'count': available_employees.count(),
             'names': [avail.employee.full_name for avail in available_employees],
             'is_full': available_employees.count() >= shift.get_max_capacity()
         }


    # Group shifts by day for template structure
    shifts_by_day = {}
    for day_code, day_name in Shift.DAY_CHOICES:
         shifts_by_day[day_name] = [s for s in all_shifts if s.day_of_week == day_code]


    if request.method == 'POST':
        form = AvailabilitySelectionForm(request.POST, employee=employee)
        if form.is_valid():
            # Use .values_list('id', flat=True) instead of just .values_list('id')
            selected_shift_ids = form.cleaned_data['selected_shifts'].values_list('id', flat=True)


            try:
                with transaction.atomic(): # Ensure database consistency
                    # 1. Delete previous availability for this employee
                    Availability.objects.filter(employee=employee).delete()

                    # 2. Create new availability records
                    new_availabilities = []
                    # Re-fetch selected shifts within transaction to lock them if needed (DB dependent)
                    shifts_to_add = Shift.objects.filter(id__in=selected_shift_ids)

                    # Fetch current counts *within* the transaction for the specific shifts being added
                    current_counts_in_txn = {
                        # Corrected dictionary comprehension - access using keys
                        item['shift_id']: item['count']
                        for item in Availability.objects.filter(shift__in=shifts_to_add).values('shift_id').annotate(count=models.Count('id'))
                    }


                    for shift in shifts_to_add:
                         # Get count from the transaction-specific data
                         count = current_counts_in_txn.get(shift.id, 0)
                         if count >= shift.get_max_capacity():
                              # This check ensures atomicity - if a shift filled between form validation and now
                              messages.error(request, f"Sorry, shift '{shift}' became full just before saving. Please review.")
                              raise ValueError("Shift capacity exceeded during transaction.") # Trigger rollback

                         new_availabilities.append(Availability(employee=employee, shift=shift))

                    Availability.objects.bulk_create(new_availabilities)

            except ValueError as e: # Handle specific error raised for rollback
                 # The message is already added, just stay on the page
                 pass # Render the form again below with the error message
            else: # Transaction succeeded
                 messages.success(request, f"Availability for {employee_name} saved successfully!")
                 # Clear session and redirect
                 request.session.pop('employee_id', None)
                 request.session.pop('employee_name', None)
                 # Redirect to the view availability page after successful save
                 return redirect('littlecaesars:view_availability')

        # If form is invalid (or transaction failed), re-render the page with errors
        # The 'form' instance already contains errors.
        context = {
            'form': form,
            'employee_name': employee_name,
            'shifts_by_day': shifts_by_day,
            'availability_data': availability_data, # Pass counts/names/full status
            'max_capacity': Shift.get_max_capacity()
        }
        return render(request, 'littlecaesars/select_availability.html', context)

    else: # GET Request
        # Pre-populate form with employee's current selections
        existing_availability_pks = Availability.objects.filter(employee=employee).values_list('shift__pk', flat=True)
        form = AvailabilitySelectionForm(employee=employee, initial={'selected_shifts': list(existing_availability_pks)})

        context = {
            'form': form,
            'employee_name': employee_name,
            'shifts_by_day': shifts_by_day,
            'availability_data': availability_data, # Pass counts/names/full status
            'max_capacity': Shift.get_max_capacity()
        }
        return render(request, 'littlecaesars/select_availability.html', context)


def view_availability(request):
    # Fetch all shifts ordered by day and time
    all_shifts = Shift.objects.order_by('day_of_week', 'time_slot')

    # Create a dictionary to hold availability grouped by shift
    # This will map shift ID to a list of employee names
    availability_by_shift = {}
    for shift in all_shifts:
        # Get all Availability objects for this shift and fetch related employee names
        available_employees = Availability.objects.filter(shift=shift).select_related('employee').order_by('submission_time')
        availability_by_shift[shift.id] = {
            'shift': shift,
            'employees': [avail.employee.full_name for avail in available_employees],
            'count': available_employees.count(),
            'max_capacity': shift.get_max_capacity(),
        }

    # Organize the data by day for the template
    availability_by_day = {}
    for day_code, day_name in Shift.DAY_CHOICES:
        availability_by_day[day_name] = []
        for shift in all_shifts:
            if shift.day_of_week == day_code:
                 if shift.id in availability_by_shift:
                      availability_by_day[day_name].append(availability_by_shift[shift.id])
                 else:
                     # Include shifts with no availability as well
                     availability_by_day[day_name].append({
                         'shift': shift,
                         'employees': [],
                         'count': 0,
                         'max_capacity': shift.get_max_capacity(),
                     })


    context = {
        'availability_by_day': availability_by_day,
    }

    return render(request, 'littlecaesars/view_availability.html', context)