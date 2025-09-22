from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Region(models.Model):
    name = models.CharField(max_length=100)
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_miles = models.PositiveIntegerField(default=35)
    truck_capacity_pounds = models.PositiveIntegerField(default=2000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class FoodBank(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='food_banks')

    # Capacity and needs
    daily_average_need_pounds = models.PositiveIntegerField(help_text="Average daily food need in pounds")
    storage_capacity_pounds = models.PositiveIntegerField(help_text="Maximum storage capacity in pounds")
    can_self_pickup = models.BooleanField(default=False, help_text="Can pick up food independently")

    # Operating hours
    open_time = models.TimeField(default='08:00')
    close_time = models.TimeField(default='17:00')
    operating_days = models.CharField(max_length=20, default='Mon-Fri')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class GroceryStore(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='grocery_stores')

    # Pickup preferences
    preferred_pickup_time_start = models.TimeField(default='08:00')
    preferred_pickup_time_end = models.TimeField(default='12:00')
    pickup_days = models.CharField(max_length=20, default='Mon-Fri')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class FoodCategory(models.Model):
    CATEGORY_CHOICES = [
        ('produce', 'Fresh Produce'),
        ('dairy', 'Dairy Products'),
        ('meat', 'Meat & Poultry'),
        ('seafood', 'Seafood'),
        ('bakery', 'Bakery Items'),
        ('frozen', 'Frozen Foods'),
        ('pantry', 'Pantry Staples'),
        ('beverages', 'Beverages'),
        ('prepared', 'Prepared Foods'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    requires_refrigeration = models.BooleanField(default=False)
    average_shelf_life_days = models.PositiveIntegerField(default=7)

    def __str__(self):
        return self.get_name_display()


class FoodDonation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grocery_store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE, related_name='donations')
    category = models.ForeignKey(FoodCategory, on_delete=models.CASCADE)
    description = models.TextField()
    quantity_pounds = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.1)])
    expiration_date = models.DateField(null=True, blank=True)
    sell_by_date = models.DateField(null=True, blank=True)

    # Scheduling
    proposed_pickup_time = models.DateTimeField(null=True, blank=True)
    confirmed_pickup_time = models.DateTimeField(null=True, blank=True)
    actual_pickup_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # AI Processing
    processed_from_email = models.BooleanField(default=False)
    original_email_content = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.grocery_store.name} - {self.category.name} ({self.quantity_pounds}lbs)"


class DeliveryRoute(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='routes')
    scheduled_date = models.DateField()
    start_time = models.TimeField(default='08:00')
    end_time = models.TimeField(default='12:00')

    driver_team = models.CharField(max_length=200, help_text="Names of the 2-person driver team")
    truck_identifier = models.CharField(max_length=50)

    total_distance_miles = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date', 'start_time']

    def __str__(self):
        return f"Route {self.scheduled_date} - {self.driver_team}"


class RouteStop(models.Model):
    STOP_TYPE_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
    ]

    route = models.ForeignKey(DeliveryRoute, on_delete=models.CASCADE, related_name='stops')
    stop_order = models.PositiveIntegerField()
    stop_type = models.CharField(max_length=10, choices=STOP_TYPE_CHOICES)

    # For pickups
    grocery_store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE, null=True, blank=True)
    donations = models.ManyToManyField(FoodDonation, blank=True)

    # For deliveries
    food_bank = models.ForeignKey(FoodBank, on_delete=models.CASCADE, null=True, blank=True)

    # Timing
    estimated_arrival_time = models.TimeField()
    actual_arrival_time = models.TimeField(null=True, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(default=15)

    # Confirmation
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by_email = models.EmailField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['route', 'stop_order']

    def __str__(self):
        if self.stop_type == 'pickup':
            return f"Pickup from {self.grocery_store.name}"
        else:
            return f"Delivery to {self.food_bank.name}"


class EmailScheduleNotification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('pickup_proposal', 'Pickup Proposal'),
        ('delivery_proposal', 'Delivery Proposal'),
        ('pickup_confirmation', 'Pickup Confirmation'),
        ('delivery_confirmation', 'Delivery Confirmation'),
        ('schedule_change', 'Schedule Change'),
        ('cancellation', 'Cancellation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPE_CHOICES)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message_body = models.TextField()

    # Related objects
    route_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, null=True, blank=True)
    donation = models.ForeignKey(FoodDonation, on_delete=models.CASCADE, null=True, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    response_received = models.BooleanField(default=False)
    response_content = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} to {self.recipient_email}"