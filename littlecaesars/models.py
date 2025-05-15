# littlecaesars/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError # Import ValidationError

class Employee(models.Model):
    full_name = models.CharField(max_length=100, unique=True)
    # Add other employee details later if needed (e.g., is_minor)

    def __str__(self):
        return self.full_name

class Shift(models.Model):
    # Represents a specific shift slot on a specific day
    # Days are represented by integers: 0=Monday, 1=Tuesday, ..., 6=Sunday
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    # Shift times
    TIME_CHOICES = [
        ('10-4', '10:00 AM - 4:00 PM'),
        ('4-10', '4:00 PM - 10:00 PM'),
    ]

    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    time_slot = models.CharField(max_length=5, choices=TIME_CHOICES)

    class Meta:
        unique_together = ('day_of_week', 'time_slot') # Each shift slot is unique
        ordering = ['day_of_week', 'time_slot'] # Keep shifts ordered

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.get_time_slot_display()}"

    @staticmethod
    def get_max_capacity():
        # Define max capacity per shift
        return 8

    @property
    def current_capacity(self):
        # Efficiently get the current number of available employees
        return self.available_employees.count()

    def is_full(self):
        # Check if the shift is at maximum capacity
        return self.current_capacity >= self.get_max_capacity()


class Availability(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='availabilities')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='available_employees')
    submission_time = models.DateTimeField(default=timezone.now) # For first-come logic

    class Meta:
        unique_together = ('employee', 'shift') # Employee can only be available once for a shift
        ordering = ['submission_time'] # Useful for first-come logic

    def __str__(self):
        return f"{self.employee.full_name} available for {self.shift}"

    # Optional: Add validation directly on the model save method (extra layer of safety)
    # def clean(self):
    #     # Check capacity before saving instance
    #     # Note: This has limitations with bulk operations and potential race conditions
    #     # The primary check should ideally be in the form/view during submission.
    #     existing_availabilities = Availability.objects.filter(shift=self.shift)
    #     # Exclude self if already exists (for updates, though we delete/recreate in the view)
    #     if self.pk:
    #         existing_availabilities = existing_availabilities.exclude(pk=self.pk)
    #
    #     if existing_availabilities.count() >= self.shift.get_max_capacity():
    #         raise ValidationError(f"Shift '{self.shift}' is already full.")

    # def save(self, *args, **kwargs):
    #     self.full_clean() # Call model validation before saving
    #     super().save(*args, **kwargs)