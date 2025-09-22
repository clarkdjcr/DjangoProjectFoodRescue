from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from foodbank.models import (
    Region, FoodBank, GroceryStore, FoodCategory,
    FoodDonation
)


class Command(BaseCommand):
    help = 'Create sample data for testing the food waste reduction platform'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create a sample region
        region, created = Region.objects.get_or_create(
            name='Metro Atlanta Food Hub',
            defaults={
                'center_latitude': Decimal('33.7490'),
                'center_longitude': Decimal('-84.3880'),
                'radius_miles': 35,
                'truck_capacity_pounds': 2000,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created region: {region.name}'))

        # Create sample food banks
        food_banks_data = [
            {
                'name': 'Atlanta Community Food Bank',
                'contact_person': 'Sarah Johnson',
                'email': 'sarah@atlantafoodbank.org',
                'phone': '(404) 555-0101',
                'address': '732 Joseph E Lowery Blvd NW, Atlanta, GA 30318',
                'latitude': Decimal('33.7701'),
                'longitude': Decimal('-84.4092'),
                'daily_average_need_pounds': 500,
                'storage_capacity_pounds': 2000,
                'can_self_pickup': True
            },
            {
                'name': 'North Fulton Community Charities',
                'contact_person': 'Michael Chen',
                'email': 'michael@nfcchelp.org',
                'phone': '(770) 555-0102',
                'address': '11270 Elkins Rd, Roswell, GA 30076',
                'latitude': Decimal('34.0232'),
                'longitude': Decimal('-84.3616'),
                'daily_average_need_pounds': 300,
                'storage_capacity_pounds': 1200,
                'can_self_pickup': False
            },
            {
                'name': 'DeKalb County Food Pantry',
                'contact_person': 'Lisa Rodriguez',
                'email': 'lisa@dekalbfood.org',
                'phone': '(404) 555-0103',
                'address': '2801 E Point St, East Point, GA 30344',
                'latitude': Decimal('33.6746'),
                'longitude': Decimal('-84.4392'),
                'daily_average_need_pounds': 400,
                'storage_capacity_pounds': 1500,
                'can_self_pickup': True
            }
        ]

        for bank_data in food_banks_data:
            food_bank, created = FoodBank.objects.get_or_create(
                name=bank_data['name'],
                region=region,
                defaults=bank_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created food bank: {food_bank.name}'))

        # Create sample grocery stores
        grocery_stores_data = [
            {
                'name': 'Kroger - Midtown',
                'contact_person': 'David Wilson',
                'email': 'david.wilson@kroger.com',
                'phone': '(404) 555-0201',
                'address': '950 W Peachtree St NW, Atlanta, GA 30309',
                'latitude': Decimal('33.7840'),
                'longitude': Decimal('-84.3907'),
            },
            {
                'name': 'Publix - Buckhead',
                'contact_person': 'Amanda Taylor',
                'email': 'amanda.taylor@publix.com',
                'phone': '(404) 555-0202',
                'address': '3637 Peachtree Rd NE, Atlanta, GA 30319',
                'latitude': Decimal('33.8429'),
                'longitude': Decimal('-84.3733'),
            },
            {
                'name': 'Whole Foods - Ponce City Market',
                'contact_person': 'Robert Martinez',
                'email': 'robert.martinez@wholefoods.com',
                'phone': '(404) 555-0203',
                'address': '650 North Ave NE, Atlanta, GA 30308',
                'latitude': Decimal('33.7725'),
                'longitude': Decimal('-84.3656'),
            },
            {
                'name': 'Fresh Market - Roswell',
                'contact_person': 'Jennifer Kim',
                'email': 'jennifer.kim@freshmarket.com',
                'phone': '(770) 555-0204',
                'address': '1205 Woodstock Rd, Roswell, GA 30075',
                'latitude': Decimal('34.0313'),
                'longitude': Decimal('-84.3445'),
            }
        ]

        for store_data in grocery_stores_data:
            grocery_store, created = GroceryStore.objects.get_or_create(
                name=store_data['name'],
                region=region,
                defaults=store_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created grocery store: {grocery_store.name}'))

        # Create sample food donations
        grocery_stores = region.grocery_stores.all()
        food_categories = FoodCategory.objects.all()

        if grocery_stores and food_categories:
            sample_donations = [
                {
                    'store': grocery_stores[0],  # Kroger Midtown
                    'category': food_categories.get(name='produce'),
                    'description': 'Mixed fresh vegetables - slightly wilted lettuce, tomatoes, carrots',
                    'quantity_pounds': Decimal('45.5'),
                    'expiration_date': (timezone.now() + timedelta(days=2)).date(),
                    'status': 'pending'
                },
                {
                    'store': grocery_stores[0],  # Kroger Midtown
                    'category': food_categories.get(name='bakery'),
                    'description': 'Day-old bread, pastries, and muffins',
                    'quantity_pounds': Decimal('12.3'),
                    'sell_by_date': (timezone.now() + timedelta(days=1)).date(),
                    'status': 'pending'
                },
                {
                    'store': grocery_stores[1],  # Publix Buckhead
                    'category': food_categories.get(name='dairy'),
                    'description': 'Milk, yogurt, and cheese approaching expiration',
                    'quantity_pounds': Decimal('23.7'),
                    'expiration_date': (timezone.now() + timedelta(days=3)).date(),
                    'status': 'confirmed'
                },
                {
                    'store': grocery_stores[2],  # Whole Foods
                    'category': food_categories.get(name='prepared'),
                    'description': 'Prepared salads and sandwiches from deli counter',
                    'quantity_pounds': Decimal('18.2'),
                    'expiration_date': timezone.now().date(),
                    'status': 'confirmed'
                },
                {
                    'store': grocery_stores[3],  # Fresh Market
                    'category': food_categories.get(name='meat'),
                    'description': 'Ground beef and chicken approaching sell-by date',
                    'quantity_pounds': Decimal('31.8'),
                    'sell_by_date': (timezone.now() + timedelta(days=1)).date(),
                    'status': 'pending'
                }
            ]

            for donation_data in sample_donations:
                donation, created = FoodDonation.objects.get_or_create(
                    grocery_store=donation_data['store'],
                    category=donation_data['category'],
                    description=donation_data['description'],
                    defaults={
                        'quantity_pounds': donation_data['quantity_pounds'],
                        'expiration_date': donation_data.get('expiration_date'),
                        'sell_by_date': donation_data.get('sell_by_date'),
                        'status': donation_data['status']
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created donation: {donation.description[:50]}... '
                            f'({donation.quantity_pounds} lbs)'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample data creation complete!\n'
                f'Region: {region.name}\n'
                f'Food Banks: {region.food_banks.count()}\n'
                f'Grocery Stores: {region.grocery_stores.count()}\n'
                f'Pending Donations: {FoodDonation.objects.filter(status="pending").count()}\n'
                f'Confirmed Donations: {FoodDonation.objects.filter(status="confirmed").count()}\n\n'
                f'You can now access the application at: http://localhost:8000/'
            )
        )