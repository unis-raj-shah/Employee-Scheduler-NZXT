"""Service for warehouse scheduling operations."""

from typing import Dict, List, Any, Optional
from metrics_service import get_metrics_summary, calculate_required_roles
from database import retrieve_employees
from inbound_service import get_incoming_data
from api_client import get_outbound_orders, get_picked_outbound_orders
from notification_service import send_schedule_email
from api_client import get_tomorrow_date_range

def get_orders_for_scheduling():
    """
    Get all orders needed for scheduling.
    
    Returns:
        Tuple of (forecast_data, forecast_dates)
    """
    try:
        # Get orders from API
        outbound_orders = get_outbound_orders()
        picked_orders = get_picked_outbound_orders()
        
        # Get incoming data using inbound_service
        incoming_data = get_incoming_data()
        total_incoming_pallets = round(incoming_data.get("incoming_pallets", 0))
        
        # Calculate forecast data
        total_shipping_pallets = sum(order.get('pallet_qty', 0) for order in outbound_orders)
        total_order_qty = sum(order.get('order_qty', 0) for order in outbound_orders)
        
        # Calculate cases to pick based on picking type and pallet qty
        cases_to_pick = 0
        for order in outbound_orders:
            picking_type = order.get('Picking Type', '')
            pallet_qty = order.get('pallet_qty', 0)
            order_qty = order.get('order_qty', 0)
            
            if picking_type in ['PIECE_PICK', 'CASE_PICK'] and pallet_qty == 0:
                cases_to_pick += order_qty
        
        # Calculate picked pallets
        total_picked_pallets = sum(order.get('pallet_qty', 0) for order in picked_orders)
        
        # Get tomorrow's date range
        tomorrow_start, tomorrow_end, _ = get_tomorrow_date_range()
        
        forecast_data = {
            'daily_shipping_pallets': total_shipping_pallets,
            'daily_incoming_pallets': total_incoming_pallets,
            'daily_order_qty': total_order_qty,
            'cases_to_pick': cases_to_pick,
            'picked_outbound_orders': picked_orders,
            'total_picked_pallets': total_picked_pallets
        }
        
        forecast_dates = {
            'start_date': tomorrow_start,
            'end_date': tomorrow_end
        }
        
        return forecast_data, forecast_dates
        
    except Exception as e:
        print(f"Error getting orders for scheduling: {str(e)}")
        # Return default values that won't cause downstream issues
        tomorrow_start, tomorrow_end, _ = get_tomorrow_date_range()
        return {
            'daily_shipping_pallets': 0,
            'daily_incoming_pallets': 0,
            'daily_order_qty': 0,
            'cases_to_pick': 0,
            'picked_outbound_orders': [],
            'total_picked_pallets': 0
        }, {
            'start_date': tomorrow_start,
            'end_date': tomorrow_end
        }

def assign_employees_to_roles(required_roles: Dict[str, Dict[str, int]]) -> Dict[str, List[str]]:
    """
    Assign employees to the calculated required roles.
    
    Args:
        required_roles: Dictionary of operations and their required role counts
        
    Returns:
        Dictionary mapping roles to lists of assigned employees
    """
    assigned_employees = {}
    
    try:
        # Flatten the nested role structure for employee matching
        flattened_roles = {}
        for operation, roles in required_roles.items():
            for role, count in roles.items():
                role_key = f"{operation}_{role}"
                flattened_roles[role_key] = count
        
        # Get employees matching the required roles
        matched_employees = retrieve_employees(flattened_roles)
        
        # For each role, assign the required number of employees
        for role, count in flattened_roles.items():
            available_employees = matched_employees.get(role, [])
            if len(available_employees) < count:
                print(f"Warning: Not enough employees for role {role}. Need {count}, found {len(available_employees)}")
            
            # Assign up to the required number of employees
            assigned_employees[role] = available_employees[:count]
    
    except Exception as e:
        print(f"Error assigning employees to roles: {e}")
    
    return assigned_employees

def run_scheduler() -> Optional[Dict[str, Any]]:
    """
    Run warehouse shift scheduler.
    
    Returns:
        Dictionary containing scheduling data or None if no data
    """
    _, _, tomorrow = get_tomorrow_date_range()
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    tomorrow_day = tomorrow.strftime('%A')
    
    metrics_summaries = get_metrics_summary()
    forecast_data, forecast_dates = get_orders_for_scheduling()
    
    if not forecast_data:
        return None
    
    required_roles = calculate_required_roles(metrics_summaries, forecast_data)
    
    # Get forecast data
    shipping_pallets = forecast_data.get("daily_shipping_pallets", 0)
    total_cases = forecast_data.get("daily_order_qty", 0)
    cases_to_pick = forecast_data.get("cases_to_pick", 0)
    
    # Calculate total picked pallets
    picked_orders = forecast_data.get("picked_outbound_orders", [])
    picked_pallets = sum(float(order.get('pallet_qty', 0)) or 0 for order in picked_orders)
    
    # Assign employees to roles
    assigned_employees = assign_employees_to_roles(required_roles)
    
    schedule_data = {
        'date': tomorrow_str,
        'day_name': tomorrow_day,
        'required_roles': required_roles,
        'assigned_employees': assigned_employees,
        'forecast_data': {
            'shipping_pallets': shipping_pallets,
            'incoming_pallets': forecast_data.get("daily_incoming_pallets", 0),
            'order_qty': total_cases,
            'cases_to_pick': cases_to_pick,
            'picked_pallets': picked_pallets
        }
    }
    
    # Send schedule emails to assigned employees
    send_schedule_email(schedule_data, assigned_employees)
    
    # Send forecast email to the team
    from notification_service import send_forecast_email
    forecast_email_data = {
        'shipping_pallets': shipping_pallets,
        'incoming_pallets': forecast_data.get("daily_incoming_pallets", 0),
        'cases_to_pick': cases_to_pick,
        'picked_pallets': picked_pallets
    }
    send_forecast_email(forecast_email_data, required_roles)
    
    return schedule_data