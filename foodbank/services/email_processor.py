import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.conf import settings

from ..models import (
    FoodDonation, FoodCategory, GroceryStore,
    DeliveryRoute, RouteStop, EmailScheduleNotification
)


class AIEmailProcessor:
    """
    AI-powered email processing service for food donations.
    This would integrate with OpenAI's API in a production environment.
    """

    def __init__(self):
        # In production, initialize OpenAI client here
        # self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        pass

    def process_email(self, email_content: str, grocery_store: GroceryStore) -> List[FoodDonation]:
        """
        Process an email from a grocery store to extract food donation information.

        Args:
            email_content: Raw email content
            grocery_store: The grocery store sending the email

        Returns:
            List of created FoodDonation objects
        """
        try:
            # In production, this would use OpenAI API
            # For now, we'll use pattern matching and mock AI processing
            extracted_items = self._extract_food_items_mock(email_content)

            donations = []
            for item in extracted_items:
                # Map extracted category to our FoodCategory model
                category = self._map_category(item.get('category', 'other'))

                if category:
                    donation = FoodDonation.objects.create(
                        grocery_store=grocery_store,
                        category=category,
                        description=item.get('description', 'Processed from email'),
                        quantity_pounds=float(item.get('quantity', 1.0)),
                        expiration_date=self._parse_date(item.get('expiration_date')),
                        sell_by_date=self._parse_date(item.get('sell_by_date')),
                        processed_from_email=True,
                        original_email_content=email_content
                    )
                    donations.append(donation)

            return donations

        except Exception as e:
            # Log error in production
            print(f"Error processing email: {e}")
            return []

    def _extract_food_items_mock(self, email_content: str) -> List[Dict]:
        """
        Mock AI extraction - in production this would use OpenAI API.
        This function attempts to extract food items using pattern matching.
        """
        items = []

        # Common patterns for food items in emails
        patterns = [
            # Pattern: "10 lbs fresh produce expires 12/25"
            r'(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\s+([^,\.]+?)(?:\s+(?:expires?|exp|expiration)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?))?',
            # Pattern: "Dairy products - 5 pounds - sell by 12/20"
            r'([^-]+?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\s*(?:-\s*(?:sell\s+by|expires?)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?))?',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, email_content, re.IGNORECASE)
            for match in matches:
                groups = match.groups()

                if len(groups) >= 2:
                    # Determine quantity and description based on pattern
                    if groups[0].replace('.', '').replace(',', '').isdigit():
                        quantity = groups[0]
                        description = groups[1].strip()
                        date_str = groups[2] if len(groups) > 2 else None
                    else:
                        description = groups[0].strip()
                        quantity = groups[1]
                        date_str = groups[2] if len(groups) > 2 else None

                    # Categorize the item
                    category = self._categorize_description(description)

                    items.append({
                        'description': description,
                        'quantity': quantity,
                        'category': category,
                        'expiration_date': date_str,
                        'sell_by_date': date_str
                    })

        # If no patterns matched, create a generic item
        if not items:
            items.append({
                'description': 'Mixed food items (requires manual review)',
                'quantity': '1.0',
                'category': 'other',
                'expiration_date': None,
                'sell_by_date': None
            })

        return items

    def _categorize_description(self, description: str) -> str:
        """
        Categorize food items based on description keywords.
        """
        desc_lower = description.lower()

        # Categorization keywords
        categories = {
            'produce': ['produce', 'vegetables', 'fruits', 'lettuce', 'tomato', 'apple', 'banana',
                       'carrot', 'onion', 'potato', 'fresh', 'organic'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'dairy'],
            'meat': ['meat', 'beef', 'chicken', 'pork', 'turkey', 'ham', 'sausage', 'ground'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'seafood', 'crab'],
            'bakery': ['bread', 'rolls', 'bakery', 'pastry', 'cake', 'cookies', 'muffins'],
            'frozen': ['frozen', 'ice cream', 'frozen food'],
            'pantry': ['canned', 'pasta', 'rice', 'cereal', 'sauce', 'soup', 'beans'],
            'beverages': ['juice', 'soda', 'water', 'beverage', 'drink'],
            'prepared': ['deli', 'prepared', 'sandwich', 'salad', 'hot food', 'cooked'],
        }

        for category, keywords in categories.items():
            if any(keyword in desc_lower for keyword in keywords):
                return category

        return 'other'

    def _map_category(self, category_name: str) -> Optional[FoodCategory]:
        """
        Map category string to FoodCategory model instance.
        """
        try:
            return FoodCategory.objects.get(name=category_name)
        except FoodCategory.DoesNotExist:
            try:
                return FoodCategory.objects.get(name='other')
            except FoodCategory.DoesNotExist:
                return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        """
        if not date_str:
            return None

        try:
            # Try different date formats
            formats = ['%m/%d/%Y', '%m/%d/%y', '%m/%d', '%Y-%m-%d']

            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)

                    # If year not specified, assume current year
                    if fmt == '%m/%d':
                        current_year = timezone.now().year
                        parsed_date = parsed_date.replace(year=current_year)

                        # If date is in the past, assume next year
                        if parsed_date.date() < timezone.now().date():
                            parsed_date = parsed_date.replace(year=current_year + 1)

                    return parsed_date.date()
                except ValueError:
                    continue

        except Exception:
            pass

        return None

    def generate_pickup_schedule(self, donations: List[FoodDonation]) -> Dict:
        """
        Generate optimized pickup and delivery schedule for donations.
        This would integrate with route optimization algorithms in production.
        """
        if not donations:
            return {}

        # Group donations by grocery store and urgency
        urgent_donations = []
        regular_donations = []

        today = timezone.now().date()

        for donation in donations:
            # Determine urgency based on expiration dates
            is_urgent = False

            if donation.expiration_date:
                days_to_expiry = (donation.expiration_date - today).days
                if days_to_expiry <= 2:
                    is_urgent = True

            if donation.sell_by_date:
                days_to_sell_by = (donation.sell_by_date - today).days
                if days_to_sell_by <= 1:
                    is_urgent = True

            if is_urgent:
                urgent_donations.append(donation)
            else:
                regular_donations.append(donation)

        # Generate suggested pickup times
        suggested_schedule = {
            'urgent_pickups': self._generate_pickup_times(urgent_donations, priority=True),
            'regular_pickups': self._generate_pickup_times(regular_donations, priority=False),
            'total_weight': sum(d.quantity_pounds for d in donations),
            'estimated_duration': self._estimate_pickup_duration(donations)
        }

        return suggested_schedule

    def _generate_pickup_times(self, donations: List[FoodDonation], priority: bool = False) -> List[Dict]:
        """
        Generate pickup time suggestions for a list of donations.
        """
        if not donations:
            return []

        pickup_times = []
        base_time = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)

        # For urgent items, schedule for next available slot
        if priority:
            base_time = base_time + timedelta(days=1)
        else:
            base_time = base_time + timedelta(days=2)

        # Group by grocery store
        stores = {}
        for donation in donations:
            store = donation.grocery_store
            if store not in stores:
                stores[store] = []
            stores[store].append(donation)

        for store, store_donations in stores.items():
            total_weight = sum(d.quantity_pounds for d in store_donations)
            estimated_duration = max(15, min(60, total_weight * 2))  # 2 minutes per pound, 15-60 min range

            pickup_times.append({
                'grocery_store': store,
                'donations': store_donations,
                'suggested_time': base_time,
                'estimated_duration_minutes': estimated_duration,
                'total_weight': total_weight,
                'priority': priority
            })

            # Space out pickup times by estimated duration + travel time
            base_time += timedelta(minutes=estimated_duration + 30)

        return pickup_times

    def _estimate_pickup_duration(self, donations: List[FoodDonation]) -> int:
        """
        Estimate total pickup duration in minutes.
        """
        total_weight = sum(d.quantity_pounds for d in donations)
        stores_count = len(set(d.grocery_store for d in donations))

        # Base time per store + time per pound
        base_time = stores_count * 20  # 20 minutes base time per store
        weight_time = total_weight * 1.5  # 1.5 minutes per pound
        travel_time = (stores_count - 1) * 15  # 15 minutes travel between stores

        return int(base_time + weight_time + travel_time)


class ScheduleNotificationService:
    """
    Service for sending schedule notifications via email.
    """

    def __init__(self):
        # In production, initialize SendGrid client here
        pass

    def send_pickup_proposal(self, pickup_info: Dict) -> bool:
        """
        Send pickup time proposal to grocery store.
        """
        try:
            grocery_store = pickup_info['grocery_store']
            suggested_time = pickup_info['suggested_time']
            donations = pickup_info['donations']

            # Create notification record
            notification = EmailScheduleNotification.objects.create(
                notification_type='pickup_proposal',
                recipient_email=grocery_store.email,
                subject=f'Pickup Confirmation Needed - {grocery_store.name}',
                message_body=self._generate_pickup_proposal_email(pickup_info)
            )

            # In production, send actual email via SendGrid
            print(f"EMAIL SENT: Pickup proposal to {grocery_store.email}")
            print(f"Suggested time: {suggested_time}")
            print(f"Donations: {len(donations)} items")

            # Mark as sent (in production, only after successful send)
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save()

            return True

        except Exception as e:
            print(f"Error sending pickup proposal: {e}")
            return False

    def _generate_pickup_proposal_email(self, pickup_info: Dict) -> str:
        """
        Generate email content for pickup proposal.
        """
        grocery_store = pickup_info['grocery_store']
        suggested_time = pickup_info['suggested_time']
        donations = pickup_info['donations']
        total_weight = pickup_info['total_weight']
        duration = pickup_info['estimated_duration_minutes']

        items_list = "\n".join([
            f"- {d.description} ({d.quantity_pounds} lbs)"
            for d in donations
        ])

        email_content = f"""
Dear {grocery_store.contact_person},

Thank you for your food donation! We have processed your request and would like to schedule a pickup.

PICKUP DETAILS:
- Store: {grocery_store.name}
- Proposed Date/Time: {suggested_time.strftime('%A, %B %d, %Y at %I:%M %p')}
- Estimated Duration: {duration} minutes
- Total Weight: {total_weight} lbs

ITEMS TO PICKUP:
{items_list}

Please reply to confirm this pickup time or let us know if you need an alternative time.

Our volunteer truck team will arrive during the confirmed window with proper refrigerated storage.

Thank you for helping reduce food waste in our community!

Best regards,
Food Rescue Hub Team

Contact: {grocery_store.phone}
"""
        return email_content.strip()