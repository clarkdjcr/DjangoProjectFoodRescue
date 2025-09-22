from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import (
    Region, FoodBank, GroceryStore, FoodDonation,
    FoodCategory, DeliveryRoute, RouteStop,
    EmailScheduleNotification
)
from .forms import (
    RegionSetupForm, FoodBankRegistrationForm,
    GroceryStoreRegistrationForm, FoodDonationForm,
    MobileFoodDonationForm, RouteConfirmationForm,
    DriverTeamAssignmentForm, EmailDonationProcessingForm
)
from .services.email_processor import AIEmailProcessor, ScheduleNotificationService
from .services.route_optimizer import RouteOptimizer
from .services.confirmation_workflow import ConfirmationWorkflowService


def home(request):
    """Homepage with regional overview"""
    regions = Region.objects.filter(is_active=True)
    context = {
        'regions': regions,
        'total_food_banks': FoodBank.objects.filter(is_active=True).count(),
        'total_grocery_stores': GroceryStore.objects.filter(is_active=True).count(),
        'recent_donations': FoodDonation.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
    }
    return render(request, 'foodbank/home.html', context)


@login_required
def region_setup(request):
    """Setup new region"""
    if request.method == 'POST':
        form = RegionSetupForm(request.POST)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region "{region.name}" created successfully!')
            return redirect('foodbank:region_dashboard', region_id=region.id)
    else:
        form = RegionSetupForm()

    return render(request, 'foodbank/region_setup.html', {'form': form})


def region_dashboard(request, region_id):
    """Dashboard for a specific region"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    # Get region statistics
    food_banks = region.food_banks.filter(is_active=True)
    grocery_stores = region.grocery_stores.filter(is_active=True)

    recent_donations = FoodDonation.objects.filter(
        grocery_store__region=region,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:10]

    active_routes = DeliveryRoute.objects.filter(
        region=region,
        scheduled_date__gte=timezone.now().date(),
        status__in=['planned', 'in_progress']
    ).order_by('scheduled_date', 'start_time')

    context = {
        'region': region,
        'food_banks': food_banks,
        'grocery_stores': grocery_stores,
        'recent_donations': recent_donations,
        'active_routes': active_routes,
        'total_capacity': food_banks.aggregate(
            total=Sum('storage_capacity_pounds')
        )['total'] or 0,
        'total_daily_need': food_banks.aggregate(
            total=Sum('daily_average_need_pounds')
        )['total'] or 0,
    }
    return render(request, 'foodbank/region_dashboard.html', context)


def food_bank_registration(request, region_id):
    """Food bank registration form"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    if request.method == 'POST':
        form = FoodBankRegistrationForm(request.POST)
        if form.is_valid():
            food_bank = form.save(commit=False)
            food_bank.region = region
            food_bank.save()
            messages.success(request, f'Food bank "{food_bank.name}" registered successfully!')
            return redirect('foodbank:region_dashboard', region_id=region.id)
    else:
        form = FoodBankRegistrationForm()

    context = {
        'form': form,
        'region': region,
        'title': 'Register Food Bank'
    }
    return render(request, 'foodbank/registration_form.html', context)


def grocery_store_registration(request, region_id):
    """Grocery store registration form"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    if request.method == 'POST':
        form = GroceryStoreRegistrationForm(request.POST)
        if form.is_valid():
            grocery_store = form.save(commit=False)
            grocery_store.region = region
            grocery_store.save()
            messages.success(request, f'Grocery store "{grocery_store.name}" registered successfully!')
            return redirect('foodbank:region_dashboard', region_id=region.id)
    else:
        form = GroceryStoreRegistrationForm()

    context = {
        'form': form,
        'region': region,
        'title': 'Register Grocery Store'
    }
    return render(request, 'foodbank/registration_form.html', context)


def food_donation_form(request, store_id):
    """Food donation form for grocery stores"""
    grocery_store = get_object_or_404(GroceryStore, id=store_id, is_active=True)

    # Detect mobile devices for simplified form
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_mobile = any(x in user_agent for x in ['mobile', 'android', 'iphone', 'ipad'])

    form_class = MobileFoodDonationForm if is_mobile else FoodDonationForm

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.grocery_store = grocery_store
            donation.save()
            messages.success(request, 'Food donation submitted successfully! You will receive pickup time confirmation soon.')
            return redirect('foodbank:food_donation_form', store_id=store_id)
    else:
        form = form_class()

    context = {
        'form': form,
        'grocery_store': grocery_store,
        'is_mobile': is_mobile,
        'recent_donations': grocery_store.donations.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:5]
    }
    return render(request, 'foodbank/food_donation_form.html', context)


@login_required
def route_planning(request, region_id):
    """Route planning and optimization interface"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    # Get pending donations for route planning
    pending_donations = FoodDonation.objects.filter(
        grocery_store__region=region,
        status='pending'
    ).order_by('expiration_date', 'sell_by_date', 'created_at')

    # Group by expiration urgency
    urgent_donations = pending_donations.filter(
        Q(expiration_date__lte=timezone.now().date() + timedelta(days=2)) |
        Q(sell_by_date__lte=timezone.now().date() + timedelta(days=1))
    )

    regular_donations = pending_donations.exclude(
        id__in=urgent_donations.values_list('id', flat=True)
    )

    # Get active routes for the region
    upcoming_routes = DeliveryRoute.objects.filter(
        region=region,
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date', 'start_time')

    context = {
        'region': region,
        'urgent_donations': urgent_donations,
        'regular_donations': regular_donations,
        'upcoming_routes': upcoming_routes,
        'food_banks': region.food_banks.filter(is_active=True),
        'grocery_stores': region.grocery_stores.filter(is_active=True),
    }
    return render(request, 'foodbank/route_planning.html', context)


@login_required
def create_route(request, region_id):
    """Create new delivery route"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    if request.method == 'POST':
        form = DriverTeamAssignmentForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route.region = region
            route.save()
            messages.success(request, f'Route created for {route.scheduled_date}')
            return redirect('foodbank:route_detail', route_id=route.id)
    else:
        form = DriverTeamAssignmentForm()

    context = {
        'form': form,
        'region': region,
        'title': 'Create New Route'
    }
    return render(request, 'foodbank/route_form.html', context)


@login_required
def route_detail(request, route_id):
    """Detailed view of a delivery route"""
    route = get_object_or_404(DeliveryRoute, id=route_id)
    stops = route.stops.order_by('stop_order')

    context = {
        'route': route,
        'stops': stops,
        'unassigned_donations': FoodDonation.objects.filter(
            grocery_store__region=route.region,
            status='pending'
        ),
        'available_food_banks': route.region.food_banks.filter(is_active=True)
    }
    return render(request, 'foodbank/route_detail.html', context)


@csrf_exempt
def confirm_pickup_delivery(request, stop_id):
    """API endpoint for confirming pickup/delivery times"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    stop = get_object_or_404(RouteStop, id=stop_id)

    try:
        data = json.loads(request.body)
        confirmation = data.get('confirmed', False)
        alternative_time = data.get('alternative_time')
        notes = data.get('notes', '')

        if confirmation:
            stop.is_confirmed = True
            stop.confirmed_at = timezone.now()
            stop.notes = notes
            stop.save()

            # Update notification
            notification = EmailScheduleNotification.objects.filter(
                route_stop=stop,
                is_sent=True
            ).first()
            if notification:
                notification.response_received = True
                notification.response_content = f"Confirmed: {notes}"
                notification.save()

            return JsonResponse({'status': 'confirmed'})
        else:
            # Handle alternative time request
            return JsonResponse({'status': 'alternative_requested'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def email_processing(request, region_id):
    """Manual email processing interface"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    if request.method == 'POST':
        form = EmailDonationProcessingForm(request.POST, region=region)
        if form.is_valid():
            email_content = form.cleaned_data['email_content']
            grocery_store = form.cleaned_data['grocery_store']

            # Use AI processor to extract donation details
            processor = AIEmailProcessor()
            donations = processor.process_email(email_content, grocery_store)

            if donations:
                # Generate pickup schedule
                schedule = processor.generate_pickup_schedule(donations)

                # Send pickup proposals
                notification_service = ScheduleNotificationService()

                for pickup_info in schedule.get('urgent_pickups', []) + schedule.get('regular_pickups', []):
                    notification_service.send_pickup_proposal(pickup_info)

                messages.success(
                    request,
                    f'Email processed successfully! Created {len(donations)} donations and sent pickup proposals.'
                )
            else:
                messages.warning(request, 'Could not extract donation information from email. Please check the content and try again.')

            return redirect('foodbank:email_processing', region_id=region.id)
    else:
        form = EmailDonationProcessingForm(region=region)

    # Get recent email-processed donations
    recent_email_donations = FoodDonation.objects.filter(
        grocery_store__region=region,
        processed_from_email=True
    ).order_by('-created_at')[:10]

    context = {
        'form': form,
        'region': region,
        'recent_email_donations': recent_email_donations
    }
    return render(request, 'foodbank/email_processing.html', context)


def donation_tracking(request, donation_id):
    """Public donation tracking page"""
    donation = get_object_or_404(FoodDonation, id=donation_id)

    # Get route information if assigned
    route_stop = RouteStop.objects.filter(
        donations=donation
    ).first()

    context = {
        'donation': donation,
        'route_stop': route_stop,
        'route': route_stop.route if route_stop else None
    }
    return render(request, 'foodbank/donation_tracking.html', context)


@login_required
def analytics_dashboard(request, region_id):
    """Analytics and reporting dashboard"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    # Date range for analytics (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Key metrics
    total_donations = FoodDonation.objects.filter(
        grocery_store__region=region,
        created_at__date__range=[start_date, end_date]
    )

    total_weight = total_donations.aggregate(
        total=Sum('quantity_pounds')
    )['total'] or 0

    completed_routes = DeliveryRoute.objects.filter(
        region=region,
        scheduled_date__range=[start_date, end_date],
        status='completed'
    ).count()

    # Food category breakdown
    category_breakdown = total_donations.values(
        'category__name'
    ).annotate(
        total_weight=Sum('quantity_pounds'),
        count=Count('id')
    ).order_by('-total_weight')

    context = {
        'region': region,
        'start_date': start_date,
        'end_date': end_date,
        'total_donations_count': total_donations.count(),
        'total_weight': total_weight,
        'completed_routes': completed_routes,
        'category_breakdown': category_breakdown,
        'avg_donation_size': total_weight / total_donations.count() if total_donations.count() > 0 else 0
    }
    return render(request, 'foodbank/analytics_dashboard.html', context)


@login_required
def optimize_route(request, region_id):
    """Optimize route with confirmed donations"""
    region = get_object_or_404(Region, id=region_id, is_active=True)

    if request.method == 'POST':
        # Get confirmed donations
        confirmed_donations = FoodDonation.objects.filter(
            grocery_store__region=region,
            status='confirmed'
        )

        if not confirmed_donations:
            messages.warning(request, 'No confirmed donations available for route optimization.')
            return redirect('foodbank:route_planning', region_id=region.id)

        # Create route optimizer
        optimizer = RouteOptimizer(region)
        route_plan = optimizer.optimize_route(list(confirmed_donations))

        if route_plan['within_capacity'] and route_plan['within_time_limit']:
            # Create the actual route
            driver_team = request.POST.get('driver_team', 'Team TBD')
            truck_identifier = request.POST.get('truck_identifier', 'Truck TBD')

            route = optimizer.create_delivery_route(route_plan, driver_team, truck_identifier)

            # Send confirmations
            confirmation_service = ConfirmationWorkflowService()
            pickup_results = confirmation_service.send_pickup_confirmations(route)
            delivery_results = confirmation_service.send_delivery_confirmations(route)

            messages.success(
                request,
                f'Route optimized and created! Sent {pickup_results["sent"]} pickup and {delivery_results["sent"]} delivery confirmations.'
            )
            return redirect('foodbank:route_detail', route_id=route.id)
        else:
            messages.error(
                request,
                f'Route optimization failed: '
                f'{"Over capacity" if not route_plan["within_capacity"] else ""} '
                f'{"Over time limit" if not route_plan["within_time_limit"] else ""}'
            )

    return redirect('foodbank:route_planning', region_id=region.id)


@login_required
def route_confirmation_status(request, route_id):
    """Check confirmation status of a route"""
    route = get_object_or_404(DeliveryRoute, id=route_id)

    confirmation_service = ConfirmationWorkflowService()
    status = confirmation_service.check_pending_confirmations(route)

    context = {
        'route': route,
        'confirmation_status': status,
        'stops': route.stops.all().order_by('stop_order')
    }
    return render(request, 'foodbank/route_confirmation_status.html', context)