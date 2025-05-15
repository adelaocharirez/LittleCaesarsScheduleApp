# littlecaesars/management/commands/populate_shifts.py
from django.core.management.base import BaseCommand
from django.db import transaction
from littlecaesars.models import Shift # Import your Shift model

class Command(BaseCommand):
    help = 'Populates the Shift table with all possible day/time combinations if it is empty.'

    @transaction.atomic # Optional: wrap in transaction for safety
    def handle(self, *args, **options):
        if Shift.objects.exists():
            self.stdout.write(self.style.WARNING('Shifts table is not empty. Skipping population.'))
            return

        self.stdout.write('Initializing shifts...')
        shifts_to_create = []
        for day_code, _ in Shift.DAY_CHOICES:
            for time_code, _ in Shift.TIME_CHOICES:
                shifts_to_create.append(Shift(day_of_week=day_code, time_slot=time_code))

        Shift.objects.bulk_create(shifts_to_create)
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(shifts_to_create)} shifts.'))