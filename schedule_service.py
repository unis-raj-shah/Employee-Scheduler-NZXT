"""Service for warehouse scheduling operations."""

from typing import Dict, List, Any, Optional
from metrics_service import get_metrics_summary, calculate_required_roles
from database import retrieve_employees, save_scheduled_employees
from inbound_service import get_incoming_data
from api_client import get_outbound_orders, get_picked_outbound_orders
from notification_service import send_schedule_email, send_combined_forecast_email
from api_client import get_tomorrow_date_range
from staffing_history import save_daily_staffing
from datetime import datetime

def get_orders_for_scheduling(target_date: Optional[datetime] = None):
    """
    Get all orders needed for scheduling.
    
    Returns:
        Tuple of (forecast_data, forecast_dates)
    """
    try:
        # Get orders from API
        outbound_orders = get_outbound_orders(target_date)
        picked_orders = get_picked_outbound_orders(target_date)
        
        # Get incoming data using inbound_service
        incoming_data = get_incoming_data(target_date)
        total_incoming_pallets = round(incoming_data.get("incoming_pallets", 0))
        
        # Calculate forecast data
        total_shipping_pallets = sum(order.get('pallet_qty', 0) for order in outbound_orders)
        total_order_qty = sum(order.get('order_qty', 0) for order in outbound_orders)
        
        # Calculate cases to pick based on picking type and pallet qty
        cases_to_pick = 0
        for order in outbound_orders:
            picking_type = order.get('picking_type', '')
            pallet_qty = order.get('pallet_qty', 0)
            order_qty = order.get('order_qty', 0)
            
            if picking_type in ['PIECE_PICK', 'CASE_PICK'] and pallet_qty == 0:
                cases_to_pick += order_qty
        
        # Calculate picked pallets
        staged_pallets = sum(order.get('pallet_qty', 0) for order in picked_orders)
        
        forecast_data = {
            'daily_shipping_pallets': total_shipping_pallets,
            'daily_incoming_pallets': total_incoming_pallets,
            'daily_order_qty': total_order_qty,
            'cases_to_pick': cases_to_pick,
            'staged_pallets': staged_pallets
        }
        
        return forecast_data, {}
        
    except Exception as e:
        print(f"Error getting orders for scheduling: {str(e)}")
        return {}, {}

def assign_employees_to_roles(required_roles: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Assign employees to the calculated required roles.
    
    Args:
        required_roles: Dictionary of roles and their required counts
        
    Returns:
        Dictionary mapping roles to lists of assigned employees
    """
    assigned_employees = {}
    
    try:
        # Flatten the nested role structure and create mapping for base roles
        flattened_roles = {}
        base_roles_lookup = {}  # Maps base roles to their required counts
        
        for operation, roles in required_roles.items():
            for role, count in roles.items():
                role_key = f"{operation}_{role}"
                flattened_roles[role_key] = count
                
                # Map base role to total count needed across all operations
                if role in base_roles_lookup:
                    base_roles_lookup[role] += count
                else:
                    base_roles_lookup[role] = count
        
        # Get employees matching the base roles (without operation prefixes)
        matched_employees = retrieve_employees(base_roles_lookup)
        
        # Create a pool of available employees by role
        employee_pools = {}
        for role, employees in matched_employees.items():
            employee_pools[role] = employees.copy()  # Make a copy to track usage
        
        # For each flattened role, assign employees from the appropriate pool
        for role_key, count in flattened_roles.items():
            # Extract base role name (everything after the last underscore)
            base_role = role_key.split('_', 1)[1] if '_' in role_key else role_key
            
            available_employees = employee_pools.get(base_role, [])
            
            if len(available_employees) < count:
                print(f"Debug - Role: {base_role}, Required: {count}, Available: {len(available_employees)}")
            
            # Assign up to the required number of employees
            assigned_count = min(count, len(available_employees))
            assigned_employees[role_key] = available_employees[:assigned_count]
            
            # Remove assigned employees from the pool to avoid double assignment
            employee_pools[base_role] = available_employees[assigned_count:]
    
    except Exception as e:
        print(f"Error assigning employees to roles: {e}")
    
    return assigned_employees

def run_scheduler() -> Optional[Dict[str, Any]]:
    """
    Run warehouse shift scheduler.
    
    Returns:
        Dictionary containing scheduling data or None if no data
    """
    tomorrow_start, tomorrow_end, day_after_start, day_after_end = get_tomorrow_date_range()
    
    tomorrow_str = tomorrow_end.strftime('%Y-%m-%d')
    tomorrow_day = tomorrow_end.strftime('%A')
    day_after_str = day_after_end.strftime('%Y-%m-%d')
    day_after_day = day_after_end.strftime('%A')
    
    metrics_summaries = get_metrics_summary()
    
    # Get orders for tomorrow using tomorrow's date range
    forecast_data_tomorrow, _ = get_orders_for_scheduling(tomorrow_start)
    
    # Get orders for day after using day after's date range
    forecast_data_day_after, _ = get_orders_for_scheduling(day_after_start)
    
    if not forecast_data_tomorrow or not forecast_data_day_after:
        return None
    
    # Calculate required roles for both days
    required_roles_tomorrow = calculate_required_roles(metrics_summaries, forecast_data_tomorrow)
    required_roles_day_after = calculate_required_roles(metrics_summaries, forecast_data_day_after)
    
    # Save daily staffing data
    save_daily_staffing(tomorrow_str, required_roles_tomorrow)
    save_daily_staffing(day_after_str, required_roles_day_after)
    
    shipping_pallets_tomorrow = forecast_data_tomorrow.get("daily_shipping_pallets", 0)
    total_cases_tomorrow = forecast_data_tomorrow.get("daily_order_qty", 0)
    cases_to_pick_tomorrow = forecast_data_tomorrow.get("cases_to_pick", 0)
    staged_pallets_tomorrow = forecast_data_tomorrow.get("staged_pallets", 0)
    
    # Process day after tomorrow's data
    shipping_pallets_day_after = forecast_data_day_after.get("daily_shipping_pallets", 0)
    total_cases_day_after = forecast_data_day_after.get("daily_order_qty", 0)
    cases_to_pick_day_after = forecast_data_day_after.get("cases_to_pick", 0)
    staged_pallets_day_after = forecast_data_day_after.get("staged_pallets", 0)
    
    # Assign employees to roles for both days
    assigned_employees_tomorrow = assign_employees_to_roles(required_roles_tomorrow)
    assigned_employees_day_after = assign_employees_to_roles(required_roles_day_after)
    
    # Save scheduled employees to database
    save_scheduled_employees(tomorrow_str, tomorrow_day, assigned_employees_tomorrow)
    save_scheduled_employees(day_after_str, day_after_day, assigned_employees_day_after)
    
    # Calculate shortages only for tomorrow
    shortages = {}
    for operation, roles in required_roles_tomorrow.items():
        for role, required_count in roles.items():
            role_key = f"{operation}_{role}"
            assigned_count = len(assigned_employees_tomorrow.get(role_key, []))
            if assigned_count < required_count:
                shortages[role_key] = required_count - assigned_count
    
    # Create schedule data for both days
    schedule_data = {
        'tomorrow': {
            'date': tomorrow_str,
            'day_name': tomorrow_day,
            'required_roles': required_roles_tomorrow,
            'assigned_employees': assigned_employees_tomorrow,
            'forecast_data': {
                'shipping_pallets': shipping_pallets_tomorrow,
                'incoming_pallets': forecast_data_tomorrow.get("daily_incoming_pallets", 0),
                'order_qty': total_cases_tomorrow,
                'cases_to_pick': cases_to_pick_tomorrow,
                'staged_pallets': staged_pallets_tomorrow
            }
        },
        'day_after': {
            'date': day_after_str,
            'day_name': day_after_day,
            'required_roles': required_roles_day_after,
            'assigned_employees': assigned_employees_day_after,
            'forecast_data': {
                'shipping_pallets': shipping_pallets_day_after,
                'incoming_pallets': forecast_data_day_after.get("daily_incoming_pallets", 0),
                'order_qty': total_cases_day_after,
                'cases_to_pick': cases_to_pick_day_after,
                'staged_pallets': staged_pallets_day_after
            }
        }
    }
    
    # Send schedule emails for both days
    send_schedule_email(schedule_data['tomorrow'], assigned_employees_tomorrow)
    send_schedule_email(schedule_data['day_after'], assigned_employees_day_after)
    
    # Send combined forecast and staffing email
    tomorrow_data = {
        'date': tomorrow_str,
        'day_name': tomorrow_day,
        'shipping_pallets': shipping_pallets_tomorrow,
        'incoming_pallets': forecast_data_tomorrow.get("daily_incoming_pallets", 0),
        'cases_to_pick': cases_to_pick_tomorrow,
        'staged_pallets': staged_pallets_tomorrow
    }
    day_after_data = {
        'date': day_after_str,
        'day_name': day_after_day,
        'shipping_pallets': shipping_pallets_day_after,
        'incoming_pallets': forecast_data_day_after.get("daily_incoming_pallets", 0),
        'cases_to_pick': cases_to_pick_day_after,
        'staged_pallets': staged_pallets_day_after
    }
    send_combined_forecast_email(tomorrow_data, day_after_data, 
                               required_roles_tomorrow, required_roles_day_after, 
                               shortages)
    
    return schedule_data