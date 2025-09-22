from django.core.management.base import BaseCommand
from foodbank.models import FoodCategory


class Command(BaseCommand):
    help = 'Create initial food categories'

    def handle(self, *args, **options):
        categories = [
            ('produce', True, 3),      # Fresh Produce, requires refrigeration, 3 days shelf life
            ('dairy', True, 7),        # Dairy Products, requires refrigeration, 7 days shelf life
            ('meat', True, 2),         # Meat & Poultry, requires refrigeration, 2 days shelf life
            ('seafood', True, 1),      # Seafood, requires refrigeration, 1 day shelf life
            ('bakery', False, 2),      # Bakery Items, no refrigeration, 2 days shelf life
            ('frozen', True, 30),      # Frozen Foods, requires refrigeration, 30 days shelf life
            ('pantry', False, 365),    # Pantry Staples, no refrigeration, 365 days shelf life
            ('beverages', False, 90),  # Beverages, no refrigeration, 90 days shelf life
            ('prepared', True, 1),     # Prepared Foods, requires refrigeration, 1 day shelf life
            ('other', False, 7),       # Other, no refrigeration, 7 days shelf life
        ]

        created_count = 0
        for name, requires_refrigeration, shelf_life_days in categories:
            category, created = FoodCategory.objects.get_or_create(
                name=name,
                defaults={
                    'requires_refrigeration': requires_refrigeration,
                    'average_shelf_life_days': shelf_life_days
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.get_name_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.get_name_display()}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new food categories')
        )