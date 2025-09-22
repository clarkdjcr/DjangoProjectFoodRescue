from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from ..models import (
    RouteStop, EmailScheduleNotification, FoodDonation,
    DeliveryRoute
)


class ConfirmationWorkflowService:
    """
    Service for managing pickup and delivery confirmation workflows.
    Handles the process of sending confirmation requests and processing responses.
    """

    def __init__(self):
        pass

    def send_pickup_confirmations(self, route: DeliveryRoute) -> Dict[str, int]:
        """
        Send pickup confirmation requests to all grocery stores in the route.

        Args:
            route: The delivery route to send confirmations for

        Returns:
            Dictionary with confirmation statistics
        """
        pickup_stops = route.stops.filter(stop_type='pickup')
        sent_count = 0
        failed_count = 0

        for stop in pickup_stops:
            try:
                success = self._send_pickup_confirmation(stop)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Error sending pickup confirmation for stop {stop.id}: {e}")
                failed_count += 1

        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': pickup_stops.count()
        }

    def send_delivery_confirmations(self, route: DeliveryRoute) -> Dict[str, int]:
        """
        Send delivery confirmation requests to all food banks in the route.

        Args:
            route: The delivery route to send confirmations for

        Returns:
            Dictionary with confirmation statistics
        """
        delivery_stops = route.stops.filter(stop_type='delivery')
        sent_count = 0
        failed_count = 0

        for stop in delivery_stops:
            try:
                success = self._send_delivery_confirmation(stop)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Error sending delivery confirmation for stop {stop.id}: {e}")
                failed_count += 1

        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': delivery_stops.count()
        }

    def _send_pickup_confirmation(self, stop: RouteStop) -> bool:
        """
        Send pickup confirmation email to grocery store.

        Args:
            stop: The pickup stop to send confirmation for

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            grocery_store = stop.grocery_store
            if not grocery_store:
                return False

            # Generate confirmation email content
            subject = f"Pickup Confirmation Required - {stop.route.scheduled_date}"
            message_body = self._generate_pickup_confirmation_email(stop)

            # Create notification record
            notification = EmailScheduleNotification.objects.create(
                notification_type='pickup_confirmation',
                recipient_email=grocery_store.email,
                subject=subject,
                message_body=message_body,
                route_stop=stop
            )

            # Send email (in production, use SendGrid)
            success = self._send_email(
                to_email=grocery_store.email,
                subject=subject,
                message=message_body,
                notification=notification
            )

            return success

        except Exception as e:
            print(f"Error in _send_pickup_confirmation: {e}")
            return False

    def _send_delivery_confirmation(self, stop: RouteStop) -> bool:
        """
        Send delivery confirmation email to food bank.

        Args:
            stop: The delivery stop to send confirmation for

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            food_bank = stop.food_bank
            if not food_bank:
                return False

            # Generate confirmation email content
            subject = f"Delivery Schedule Confirmation - {stop.route.scheduled_date}"
            message_body = self._generate_delivery_confirmation_email(stop)

            # Create notification record
            notification = EmailScheduleNotification.objects.create(
                notification_type='delivery_confirmation',
                recipient_email=food_bank.email,
                subject=subject,
                message_body=message_body,
                route_stop=stop
            )

            # Send email (in production, use SendGrid)
            success = self._send_email(
                to_email=food_bank.email,
                subject=subject,
                message=message_body,
                notification=notification
            )

            return success

        except Exception as e:
            print(f"Error in _send_delivery_confirmation: {e}")
            return False

    def _generate_pickup_confirmation_email(self, stop: RouteStop) -> str:
        """Generate pickup confirmation email content."""
        grocery_store = stop.grocery_store
        route = stop.route
        donations = stop.donations.all()

        items_list = "\n".join([
            f"- {donation.category.name}: {donation.description} ({donation.quantity_pounds} lbs)"
            for donation in donations
        ])

        total_weight = sum(donation.quantity_pounds for donation in donations)

        confirm_url = f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/api/stop/{stop.id}/confirm/"

        email_content = f"""
Dear {grocery_store.contact_person},

We have scheduled a pickup from your store for the following items:

PICKUP DETAILS:
- Store: {grocery_store.name}
- Date: {route.scheduled_date.strftime('%A, %B %d, %Y')}
- Estimated Arrival Time: {stop.estimated_arrival_time.strftime('%I:%M %p')}
- Estimated Duration: {stop.estimated_duration_minutes} minutes
- Driver Team: {route.driver_team}
- Truck: {route.truck_identifier}

ITEMS TO PICKUP:
{items_list}

Total Weight: {total_weight} lbs

CONFIRMATION REQUIRED:
Please confirm this pickup time by replying to this email with:
- "CONFIRMED" if the time works for you
- "RESCHEDULE" with alternative times if needed
- Any special instructions for our driver team

Our volunteer drivers will arrive with proper refrigerated storage and will handle all items with care.

If you have any questions, please contact us at:
Phone: {grocery_store.phone}
Email: {grocery_store.email}

Thank you for helping reduce food waste in our community!

Best regards,
Food Rescue Hub Team

Route ID: {route.id}
Stop ID: {stop.id}
"""
        return email_content.strip()

    def _generate_delivery_confirmation_email(self, stop: RouteStop) -> str:
        """Generate delivery confirmation email content."""
        food_bank = stop.food_bank
        route = stop.route
        donations = stop.donations.all()

        # Group donations by category for easier reading
        categories = {}
        for donation in donations:
            category = donation.category.name
            if category not in categories:
                categories[category] = []
            categories[category].append(donation)

        items_by_category = []
        total_weight = 0

        for category, items in categories.items():
            category_weight = sum(item.quantity_pounds for item in items)
            total_weight += category_weight
            items_by_category.append(f"- {category}: {category_weight} lbs")

        items_list = "\n".join(items_by_category)

        email_content = f"""
Dear {food_bank.contact_person},

We have scheduled a food delivery to your food bank:

DELIVERY DETAILS:
- Food Bank: {food_bank.name}
- Date: {route.scheduled_date.strftime('%A, %B %d, %Y')}
- Estimated Arrival Time: {stop.estimated_arrival_time.strftime('%I:%M %p')}
- Estimated Duration: {stop.estimated_duration_minutes} minutes
- Driver Team: {route.driver_team}
- Truck: {route.truck_identifier}

FOOD ITEMS TO DELIVER:
{items_list}

Total Weight: {total_weight} lbs

CONFIRMATION REQUIRED:
Please confirm this delivery time by replying to this email with:
- "CONFIRMED" if the time works for you
- "RESCHEDULE" with alternative times if needed
- Any special receiving instructions

Please ensure you have adequate storage space and staff available to receive the delivery.

RECEIVING INSTRUCTIONS:
- Our team will arrive with proper refrigerated storage
- Please have staff available to help unload
- Refrigerated items should be stored immediately
- We'll provide a delivery receipt for your records

If you have questions or need to reschedule, please contact us immediately.

Contact Information:
Phone: {food_bank.phone}
Email: {food_bank.email}

Thank you for serving our community!

Best regards,
Food Rescue Hub Team

Route ID: {route.id}
Stop ID: {stop.id}
"""
        return email_content.strip()

    def _send_email(self, to_email: str, subject: str, message: str, notification: EmailScheduleNotification) -> bool:
        """
        Send email using Django's email backend.
        In production, this would use SendGrid or similar service.
        """
        try:
            # For development, we'll just print to console and mark as sent
            print(f"\n--- EMAIL SENT ---")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Message:\n{message}")
            print(f"--- END EMAIL ---\n")

            # In production, use SendGrid:
            # send_mail(
            #     subject=subject,
            #     message=message,
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[to_email],
            #     fail_silently=False,
            # )

            # Mark notification as sent
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save()

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def process_email_response(self, stop_id: int, response_content: str) -> Dict[str, any]:
        """
        Process email response for pickup/delivery confirmation.

        Args:
            stop_id: ID of the route stop
            response_content: Content of the email response

        Returns:
            Dictionary with processing results
        """
        try:
            stop = RouteStop.objects.get(id=stop_id)
            response_lower = response_content.lower().strip()

            result = {
                'stop_id': stop_id,
                'processed': False,
                'action': None,
                'message': ''
            }

            if 'confirmed' in response_lower:
                # Confirmation received
                stop.is_confirmed = True
                stop.confirmed_at = timezone.now()
                stop.save()

                # Update notification
                notification = EmailScheduleNotification.objects.filter(
                    route_stop=stop,
                    is_sent=True
                ).first()

                if notification:
                    notification.response_received = True
                    notification.response_content = response_content
                    notification.save()

                result.update({
                    'processed': True,
                    'action': 'confirmed',
                    'message': 'Pickup/delivery confirmed successfully'
                })

            elif 'reschedule' in response_lower:
                # Reschedule request
                stop.notes = f"Reschedule requested: {response_content}"
                stop.save()

                result.update({
                    'processed': True,
                    'action': 'reschedule_requested',
                    'message': 'Reschedule request received - manual review required'
                })

            else:
                # Generic response
                stop.notes = f"Response received: {response_content}"
                stop.save()

                result.update({
                    'processed': True,
                    'action': 'response_recorded',
                    'message': 'Response recorded - may require manual review'
                })

            return result

        except RouteStop.DoesNotExist:
            return {
                'stop_id': stop_id,
                'processed': False,
                'action': None,
                'message': 'Route stop not found'
            }
        except Exception as e:
            return {
                'stop_id': stop_id,
                'processed': False,
                'action': None,
                'message': f'Error processing response: {str(e)}'
            }

    def check_pending_confirmations(self, route: DeliveryRoute) -> Dict[str, any]:
        """
        Check status of pending confirmations for a route.

        Args:
            route: The delivery route to check

        Returns:
            Dictionary with confirmation status
        """
        stops = route.stops.all()

        total_stops = stops.count()
        confirmed_stops = stops.filter(is_confirmed=True).count()
        pending_stops = total_stops - confirmed_stops

        pickup_stops = stops.filter(stop_type='pickup')
        delivery_stops = stops.filter(stop_type='delivery')

        confirmed_pickups = pickup_stops.filter(is_confirmed=True).count()
        confirmed_deliveries = delivery_stops.filter(is_confirmed=True).count()

        status = {
            'route_id': route.id,
            'total_stops': total_stops,
            'confirmed_stops': confirmed_stops,
            'pending_stops': pending_stops,
            'confirmation_rate': (confirmed_stops / total_stops * 100) if total_stops > 0 else 0,
            'pickup_confirmations': {
                'total': pickup_stops.count(),
                'confirmed': confirmed_pickups,
                'pending': pickup_stops.count() - confirmed_pickups
            },
            'delivery_confirmations': {
                'total': delivery_stops.count(),
                'confirmed': confirmed_deliveries,
                'pending': delivery_stops.count() - confirmed_deliveries
            },
            'ready_for_execution': pending_stops == 0
        }

        return status

    def send_schedule_change_notifications(self, route: DeliveryRoute, change_reason: str) -> Dict[str, int]:
        """
        Send notifications about schedule changes to all parties.

        Args:
            route: The route that has been changed
            change_reason: Reason for the schedule change

        Returns:
            Dictionary with notification statistics
        """
        stops = route.stops.all()
        sent_count = 0
        failed_count = 0

        for stop in stops:
            try:
                if stop.stop_type == 'pickup':
                    recipient_email = stop.grocery_store.email
                    recipient_name = stop.grocery_store.contact_person
                else:
                    recipient_email = stop.food_bank.email
                    recipient_name = stop.food_bank.contact_person

                subject = f"Schedule Change Notification - {route.scheduled_date}"
                message_body = self._generate_schedule_change_email(stop, change_reason)

                notification = EmailScheduleNotification.objects.create(
                    notification_type='schedule_change',
                    recipient_email=recipient_email,
                    subject=subject,
                    message_body=message_body,
                    route_stop=stop
                )

                success = self._send_email(
                    to_email=recipient_email,
                    subject=subject,
                    message=message_body,
                    notification=notification
                )

                if success:
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"Error sending schedule change notification: {e}")
                failed_count += 1

        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': stops.count()
        }

    def _generate_schedule_change_email(self, stop: RouteStop, change_reason: str) -> str:
        """Generate schedule change notification email content."""
        route = stop.route

        if stop.stop_type == 'pickup':
            location = stop.grocery_store
            action = "pickup"
        else:
            location = stop.food_bank
            action = "delivery"

        email_content = f"""
Dear {location.contact_person},

This is an important notification regarding a schedule change for your {action} appointment.

ORIGINAL SCHEDULE:
- Date: {route.scheduled_date.strftime('%A, %B %d, %Y')}
- Time: {stop.estimated_arrival_time.strftime('%I:%M %p')}

CHANGE REASON:
{change_reason}

NEW SCHEDULE:
We will contact you shortly with the updated schedule information.

IMMEDIATE ACTION REQUIRED:
Please confirm your availability for alternative times by replying to this email or calling us directly.

We apologize for any inconvenience this may cause and appreciate your flexibility in helping us serve the community.

Contact Information:
Route Manager: {route.driver_team}
Phone: {location.phone}

Thank you for your understanding.

Best regards,
Food Rescue Hub Team

Route ID: {route.id}
"""
        return email_content.strip()