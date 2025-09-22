from django.contrib import admin
from .models import (
    Region, FoodBank, GroceryStore, FoodCategory,
    FoodDonation, DeliveryRoute, RouteStop,
    EmailScheduleNotification
)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'radius_miles', 'truck_capacity_pounds', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(FoodBank)
class FoodBankAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'contact_person', 'email', 'daily_average_need_pounds', 'can_self_pickup', 'is_active']
    list_filter = ['region', 'can_self_pickup', 'is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['region', 'name']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'region')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Capacity & Operations', {
            'fields': ('daily_average_need_pounds', 'storage_capacity_pounds', 'can_self_pickup')
        }),
        ('Operating Hours', {
            'fields': ('open_time', 'close_time', 'operating_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(GroceryStore)
class GroceryStoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'contact_person', 'email', 'preferred_pickup_time_start', 'is_active']
    list_filter = ['region', 'is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['region', 'name']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'region')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Pickup Preferences', {
            'fields': ('preferred_pickup_time_start', 'preferred_pickup_time_end', 'pickup_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'requires_refrigeration', 'average_shelf_life_days']
    list_filter = ['requires_refrigeration']
    ordering = ['name']


@admin.register(FoodDonation)
class FoodDonationAdmin(admin.ModelAdmin):
    list_display = ['grocery_store', 'category', 'quantity_pounds', 'status', 'expiration_date', 'created_at']
    list_filter = ['status', 'category', 'processed_from_email', 'created_at', 'expiration_date']
    search_fields = ['grocery_store__name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Donation Details', {
            'fields': ('grocery_store', 'category', 'description', 'quantity_pounds')
        }),
        ('Dates', {
            'fields': ('expiration_date', 'sell_by_date')
        }),
        ('Scheduling', {
            'fields': ('proposed_pickup_time', 'confirmed_pickup_time', 'actual_pickup_time', 'status')
        }),
        ('AI Processing', {
            'fields': ('processed_from_email', 'original_email_content'),
            'classes': ['collapse']
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 0
    ordering = ['stop_order']
    fields = ['stop_order', 'stop_type', 'grocery_store', 'food_bank', 'estimated_arrival_time', 'is_confirmed']
    readonly_fields = ['is_confirmed']


@admin.register(DeliveryRoute)
class DeliveryRouteAdmin(admin.ModelAdmin):
    list_display = ['scheduled_date', 'region', 'driver_team', 'status', 'start_time', 'total_distance_miles']
    list_filter = ['status', 'region', 'scheduled_date']
    search_fields = ['driver_team', 'truck_identifier']
    ordering = ['-scheduled_date', 'start_time']
    inlines = [RouteStopInline]
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Route Information', {
            'fields': ('region', 'scheduled_date', 'start_time', 'end_time', 'status')
        }),
        ('Team Assignment', {
            'fields': ('driver_team', 'truck_identifier')
        }),
        ('Route Metrics', {
            'fields': ('total_distance_miles', 'estimated_duration_minutes')
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'stop_order', 'stop_type', 'get_location', 'estimated_arrival_time', 'is_confirmed']
    list_filter = ['stop_type', 'is_confirmed', 'route__scheduled_date']
    search_fields = ['route__driver_team', 'grocery_store__name', 'food_bank__name']
    ordering = ['route__scheduled_date', 'route', 'stop_order']

    def get_location(self, obj):
        if obj.stop_type == 'pickup':
            return obj.grocery_store.name if obj.grocery_store else 'Unknown'
        else:
            return obj.food_bank.name if obj.food_bank else 'Unknown'
    get_location.short_description = 'Location'


@admin.register(EmailScheduleNotification)
class EmailScheduleNotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'recipient_email', 'is_sent', 'response_received', 'created_at']
    list_filter = ['notification_type', 'is_sent', 'response_received', 'created_at']
    search_fields = ['recipient_email', 'subject']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Notification Details', {
            'fields': ('notification_type', 'recipient_email', 'subject')
        }),
        ('Message', {
            'fields': ('message_body',)
        }),
        ('Related Objects', {
            'fields': ('route_stop', 'donation'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'response_received', 'response_content')
        }),
        ('System Info', {
            'fields': ('created_at',)
        })
    )