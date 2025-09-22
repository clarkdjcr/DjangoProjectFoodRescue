from django.urls import path
from . import views

app_name = 'foodbank'

urlpatterns = [
    # Home and region management
    path('', views.home, name='home'),
    path('region/setup/', views.region_setup, name='region_setup'),
    path('region/<int:region_id>/', views.region_dashboard, name='region_dashboard'),

    # Registration forms
    path('region/<int:region_id>/food-bank/register/', views.food_bank_registration, name='food_bank_registration'),
    path('region/<int:region_id>/grocery-store/register/', views.grocery_store_registration, name='grocery_store_registration'),

    # Food donation
    path('store/<int:store_id>/donate/', views.food_donation_form, name='food_donation_form'),
    path('donation/<uuid:donation_id>/track/', views.donation_tracking, name='donation_tracking'),

    # Route management
    path('region/<int:region_id>/routes/', views.route_planning, name='route_planning'),
    path('region/<int:region_id>/routes/create/', views.create_route, name='create_route'),
    path('region/<int:region_id>/routes/optimize/', views.optimize_route, name='optimize_route'),
    path('route/<uuid:route_id>/', views.route_detail, name='route_detail'),
    path('route/<uuid:route_id>/confirmations/', views.route_confirmation_status, name='route_confirmation_status'),

    # API endpoints
    path('api/stop/<int:stop_id>/confirm/', views.confirm_pickup_delivery, name='confirm_pickup_delivery'),

    # Email processing
    path('region/<int:region_id>/email-processing/', views.email_processing, name='email_processing'),

    # Analytics
    path('region/<int:region_id>/analytics/', views.analytics_dashboard, name='analytics_dashboard'),
]