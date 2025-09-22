import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from django.utils import timezone
from geopy.distance import geodesic

from ..models import (
    Region, FoodBank, GroceryStore, FoodDonation,
    DeliveryRoute, RouteStop
)


class RouteOptimizer:
    """
    Route optimization service for minimizing travel time and maximizing efficiency.
    Uses basic optimization algorithms - in production could integrate with Google OR-Tools
    or similar optimization libraries.
    """

    def __init__(self, region: Region):
        self.region = region
        self.truck_capacity = region.truck_capacity_pounds
        self.max_duration_hours = 4  # 4-hour work window (8:00-12:00)

    def optimize_route(self, donations: List[FoodDonation], target_date: datetime.date = None) -> Dict:
        """
        Optimize pickup and delivery routes for given donations.

        Args:
            donations: List of confirmed donations to include in route
            target_date: Target date for the route (defaults to tomorrow)

        Returns:
            Dictionary with optimized route information
        """
        if target_date is None:
            target_date = (timezone.now() + timedelta(days=1)).date()

        # Group donations by grocery store
        store_donations = self._group_donations_by_store(donations)

        # Get available food banks
        food_banks = list(self.region.food_banks.filter(is_active=True))

        # Calculate optimal pickup sequence
        pickup_sequence = self._optimize_pickup_sequence(store_donations)

        # Allocate food to food banks based on needs and capacity
        food_allocation = self._allocate_food_to_banks(donations, food_banks)

        # Generate delivery sequence
        delivery_sequence = self._optimize_delivery_sequence(food_allocation)

        # Create optimized route
        route_data = self._create_route_plan(
            pickup_sequence, delivery_sequence, target_date
        )

        return route_data

    def _group_donations_by_store(self, donations: List[FoodDonation]) -> Dict[GroceryStore, List[FoodDonation]]:
        """Group donations by grocery store."""
        store_donations = {}
        for donation in donations:
            store = donation.grocery_store
            if store not in store_donations:
                store_donations[store] = []
            store_donations[store].append(donation)
        return store_donations

    def _optimize_pickup_sequence(self, store_donations: Dict[GroceryStore, List[FoodDonation]]) -> List[Dict]:
        """
        Optimize the sequence of pickup stops using nearest neighbor algorithm.
        """
        if not store_donations:
            return []

        # Start from the region center
        current_location = (float(self.region.center_latitude), float(self.region.center_longitude))
        unvisited_stores = list(store_donations.keys())
        pickup_sequence = []
        current_time = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)

        # Add one day if we're planning for tomorrow
        current_time = current_time + timedelta(days=1)

        while unvisited_stores:
            # Find nearest store
            nearest_store = self._find_nearest_store(current_location, unvisited_stores)
            unvisited_stores.remove(nearest_store)

            # Calculate travel time and pickup duration
            travel_time = self._calculate_travel_time(current_location, nearest_store)
            pickup_duration = self._estimate_pickup_duration(store_donations[nearest_store])

            current_time += timedelta(minutes=travel_time)

            pickup_info = {
                'store': nearest_store,
                'donations': store_donations[nearest_store],
                'arrival_time': current_time,
                'pickup_duration': pickup_duration,
                'total_weight': sum(d.quantity_pounds for d in store_donations[nearest_store])
            }

            pickup_sequence.append(pickup_info)

            # Update current location and time
            current_location = (float(nearest_store.latitude), float(nearest_store.longitude))
            current_time += timedelta(minutes=pickup_duration)

        return pickup_sequence

    def _find_nearest_store(self, current_location: Tuple[float, float], stores: List[GroceryStore]) -> GroceryStore:
        """Find the nearest grocery store to current location."""
        min_distance = float('inf')
        nearest_store = None

        for store in stores:
            store_location = (float(store.latitude), float(store.longitude))
            distance = geodesic(current_location, store_location).miles

            if distance < min_distance:
                min_distance = distance
                nearest_store = store

        return nearest_store

    def _calculate_travel_time(self, from_location: Tuple[float, float], to_store: GroceryStore) -> int:
        """Calculate travel time in minutes between two locations."""
        to_location = (float(to_store.latitude), float(to_store.longitude))
        distance_miles = geodesic(from_location, to_location).miles

        # Assume average speed of 25 mph in urban areas
        travel_time_hours = distance_miles / 25
        travel_time_minutes = int(travel_time_hours * 60)

        # Add buffer time for urban driving
        return max(5, travel_time_minutes + 5)  # Minimum 5 minutes, plus 5-minute buffer

    def _estimate_pickup_duration(self, donations: List[FoodDonation]) -> int:
        """Estimate pickup duration in minutes based on donation size and count."""
        total_weight = sum(d.quantity_pounds for d in donations)
        item_count = len(donations)

        # Base time + time per item + time per pound
        base_time = 10  # 10 minutes base time
        item_time = item_count * 2  # 2 minutes per item
        weight_time = total_weight * 0.5  # 30 seconds per pound

        return max(15, int(base_time + item_time + weight_time))  # Minimum 15 minutes

    def _allocate_food_to_banks(self, donations: List[FoodDonation], food_banks: List[FoodBank]) -> Dict[FoodBank, List[FoodDonation]]:
        """
        Allocate food donations to food banks based on capacity and needs.
        Uses a weighted allocation algorithm.
        """
        if not food_banks:
            return {}

        # Calculate total daily needs and capacities
        total_daily_need = sum(bank.daily_average_need_pounds for bank in food_banks)
        total_capacity = sum(bank.storage_capacity_pounds for bank in food_banks)

        # Sort donations by urgency (expiration date)
        sorted_donations = sorted(donations, key=lambda d: d.expiration_date or timezone.now().date() + timedelta(days=365))

        # Initialize allocation
        bank_allocation = {bank: [] for bank in food_banks}
        bank_current_weight = {bank: 0 for bank in food_banks}

        for donation in sorted_donations:
            # Find best bank for this donation
            best_bank = self._find_best_bank_for_donation(
                donation, food_banks, bank_current_weight, total_daily_need
            )

            if best_bank:
                bank_allocation[best_bank].append(donation)
                bank_current_weight[best_bank] += donation.quantity_pounds

        return bank_allocation

    def _find_best_bank_for_donation(self, donation: FoodDonation, food_banks: List[FoodBank],
                                   current_weights: Dict[FoodBank, float], total_daily_need: float) -> Optional[FoodBank]:
        """Find the best food bank for a specific donation."""
        best_bank = None
        best_score = -1

        for bank in food_banks:
            # Check if bank has capacity
            remaining_capacity = bank.storage_capacity_pounds - current_weights[bank]
            if remaining_capacity < donation.quantity_pounds:
                continue

            # Calculate allocation score based on need ratio and capacity utilization
            need_ratio = bank.daily_average_need_pounds / total_daily_need if total_daily_need > 0 else 0
            capacity_utilization = current_weights[bank] / bank.storage_capacity_pounds

            # Prefer banks with higher need ratio and lower current utilization
            score = need_ratio * (1 - capacity_utilization)

            # Bonus for banks that can self-pickup (reduces truck load)
            if bank.can_self_pickup and donation.quantity_pounds > 50:
                score *= 1.2

            if score > best_score:
                best_score = score
                best_bank = bank

        return best_bank

    def _optimize_delivery_sequence(self, food_allocation: Dict[FoodBank, List[FoodDonation]]) -> List[Dict]:
        """Optimize delivery sequence using nearest neighbor algorithm."""
        delivery_sequence = []
        current_location = (float(self.region.center_latitude), float(self.region.center_longitude))

        # Filter out banks with no allocations
        banks_with_food = {bank: donations for bank, donations in food_allocation.items() if donations}

        unvisited_banks = list(banks_with_food.keys())

        while unvisited_banks:
            # Find nearest bank
            nearest_bank = self._find_nearest_bank(current_location, unvisited_banks)
            unvisited_banks.remove(nearest_bank)

            # Calculate travel time and delivery duration
            travel_time = self._calculate_travel_time_to_bank(current_location, nearest_bank)
            delivery_duration = self._estimate_delivery_duration(banks_with_food[nearest_bank])

            delivery_info = {
                'food_bank': nearest_bank,
                'donations': banks_with_food[nearest_bank],
                'travel_time': travel_time,
                'delivery_duration': delivery_duration,
                'total_weight': sum(d.quantity_pounds for d in banks_with_food[nearest_bank])
            }

            delivery_sequence.append(delivery_info)

            # Update current location
            current_location = (float(nearest_bank.latitude), float(nearest_bank.longitude))

        return delivery_sequence

    def _find_nearest_bank(self, current_location: Tuple[float, float], banks: List[FoodBank]) -> FoodBank:
        """Find the nearest food bank to current location."""
        min_distance = float('inf')
        nearest_bank = None

        for bank in banks:
            bank_location = (float(bank.latitude), float(bank.longitude))
            distance = geodesic(current_location, bank_location).miles

            if distance < min_distance:
                min_distance = distance
                nearest_bank = bank

        return nearest_bank

    def _calculate_travel_time_to_bank(self, from_location: Tuple[float, float], to_bank: FoodBank) -> int:
        """Calculate travel time to food bank."""
        to_location = (float(to_bank.latitude), float(to_bank.longitude))
        distance_miles = geodesic(from_location, to_location).miles

        # Assume average speed of 25 mph
        travel_time_hours = distance_miles / 25
        travel_time_minutes = int(travel_time_hours * 60)

        return max(5, travel_time_minutes + 5)

    def _estimate_delivery_duration(self, donations: List[FoodDonation]) -> int:
        """Estimate delivery duration in minutes."""
        total_weight = sum(d.quantity_pounds for d in donations)
        item_count = len(donations)

        # Base time + time per item + time per pound + unloading time
        base_time = 15  # 15 minutes base time for delivery
        item_time = item_count * 3  # 3 minutes per item category
        weight_time = total_weight * 0.8  # 48 seconds per pound
        unloading_time = 10  # 10 minutes for unloading and paperwork

        return max(20, int(base_time + item_time + weight_time + unloading_time))

    def _create_route_plan(self, pickup_sequence: List[Dict], delivery_sequence: List[Dict],
                          target_date: datetime.date) -> Dict:
        """Create comprehensive route plan."""
        total_distance = 0
        total_duration = 0
        current_time = timezone.now().replace(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour=8,
            minute=0,
            second=0,
            microsecond=0
        )

        # Process pickups
        for pickup in pickup_sequence:
            pickup['estimated_arrival'] = current_time
            current_time += timedelta(minutes=pickup['pickup_duration'])
            total_duration += pickup['pickup_duration']

        # Process deliveries
        for delivery in delivery_sequence:
            current_time += timedelta(minutes=delivery['travel_time'])
            delivery['estimated_arrival'] = current_time
            current_time += timedelta(minutes=delivery['delivery_duration'])
            total_duration += delivery['travel_time'] + delivery['delivery_duration']

        # Calculate total weight and validate capacity
        total_weight = sum(
            pickup['total_weight'] for pickup in pickup_sequence
        )

        route_plan = {
            'target_date': target_date,
            'pickup_sequence': pickup_sequence,
            'delivery_sequence': delivery_sequence,
            'total_weight_pounds': total_weight,
            'total_duration_minutes': total_duration,
            'estimated_completion_time': current_time,
            'within_capacity': total_weight <= self.truck_capacity,
            'within_time_limit': total_duration <= (self.max_duration_hours * 60),
            'efficiency_score': self._calculate_efficiency_score(pickup_sequence, delivery_sequence)
        }

        return route_plan

    def _calculate_efficiency_score(self, pickup_sequence: List[Dict], delivery_sequence: List[Dict]) -> float:
        """Calculate route efficiency score (0-100)."""
        if not pickup_sequence and not delivery_sequence:
            return 0

        # Factors: distance optimization, time utilization, capacity utilization
        total_stops = len(pickup_sequence) + len(delivery_sequence)
        total_weight = sum(pickup['total_weight'] for pickup in pickup_sequence)

        # Distance efficiency (inverse of total distance)
        distance_score = min(100, 1000 / max(1, total_stops * 5))  # Rough approximation

        # Capacity utilization
        capacity_score = min(100, (total_weight / self.truck_capacity) * 100)

        # Time efficiency
        total_duration = sum(pickup['pickup_duration'] for pickup in pickup_sequence) + \
                        sum(delivery['delivery_duration'] for delivery in delivery_sequence)
        time_score = min(100, (total_duration / (self.max_duration_hours * 60)) * 100)

        # Weighted average
        efficiency_score = (distance_score * 0.3 + capacity_score * 0.4 + time_score * 0.3)

        return round(efficiency_score, 1)

    def create_delivery_route(self, route_plan: Dict, driver_team: str, truck_identifier: str) -> DeliveryRoute:
        """Create a DeliveryRoute object from the optimized route plan."""
        route = DeliveryRoute.objects.create(
            region=self.region,
            scheduled_date=route_plan['target_date'],
            start_time=timezone.now().replace(hour=8, minute=0, second=0, microsecond=0).time(),
            end_time=route_plan['estimated_completion_time'].time(),
            driver_team=driver_team,
            truck_identifier=truck_identifier,
            total_distance_miles=0,  # Would calculate from coordinates in production
            estimated_duration_minutes=route_plan['total_duration_minutes']
        )

        # Create pickup stops
        stop_order = 1
        for pickup in route_plan['pickup_sequence']:
            stop = RouteStop.objects.create(
                route=route,
                stop_order=stop_order,
                stop_type='pickup',
                grocery_store=pickup['store'],
                estimated_arrival_time=pickup['arrival_time'].time(),
                estimated_duration_minutes=pickup['pickup_duration']
            )
            # Add donations to the stop
            stop.donations.set(pickup['donations'])
            stop_order += 1

        # Create delivery stops
        for delivery in route_plan['delivery_sequence']:
            stop = RouteStop.objects.create(
                route=route,
                stop_order=stop_order,
                stop_type='delivery',
                food_bank=delivery['food_bank'],
                estimated_arrival_time=delivery['estimated_arrival'].time(),
                estimated_duration_minutes=delivery['delivery_duration']
            )
            # Add donations to the stop
            stop.donations.set(delivery['donations'])
            stop_order += 1

        return route