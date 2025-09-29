from django.core.management.base import BaseCommand
from django.db import transaction

from foodbank.models import (
    Region, FoodBank, GroceryStore, FoodCategory,
    FoodDonation
)


class Command(BaseCommand):
    help = 'Clear all sample data from the food waste reduction platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all sample data',
        )
        parser.add_argument(
            '--keep-categories',
            action='store_true',
            help='Keep food categories (only delete regions, stores, banks, donations)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL sample data including:\n'
                    '- Regions\n'
                    '- Food Banks\n'
                    '- Grocery Stores\n'
                    '- Food Donations\n'
                    '- Food Categories (unless --keep-categories is used)\n\n'
                    'To proceed, run: python manage.py clear_sample_data --confirm'
                )
            )
            return

        self.stdout.write('Clearing sample data...')

        with transaction.atomic():
            # Count items before deletion
            donation_count = FoodDonation.objects.count()
            grocery_count = GroceryStore.objects.count()
            foodbank_count = FoodBank.objects.count()
            region_count = Region.objects.count()
            category_count = FoodCategory.objects.count()

            # Delete in order to avoid foreign key constraints
            FoodDonation.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {donation_count} food donations')
            )

            GroceryStore.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {grocery_count} grocery stores')
            )

            FoodBank.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {foodbank_count} food banks')
            )

            Region.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {region_count} regions')
            )

            if not options['keep_categories']:
                FoodCategory.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {category_count} food categories')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Kept {category_count} food categories')
                )

        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Sample data cleared successfully!\n'
                'Your database is now clean and ready for fresh data.'
            )
        )