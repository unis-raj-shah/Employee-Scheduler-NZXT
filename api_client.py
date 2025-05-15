"""Client for external API services."""

import requests
import pandas as pd
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from config import WISE_API_HEADERS, DEFAULT_CUSTOMER_ID

def get_tomorrow_date_range(days_ahead: int = 1) -> Tuple[datetime, datetime, datetime]:
    """
    Get tomorrow's date range for API requests.
    
    Args:
        days_ahead: Number of days ahead to calculate
        
    Returns:
        Tuple of (start_datetime, end_datetime, target_date)
    """
    target_date = datetime.now() + timedelta(days=days_ahead)
    start_datetime = target_date.replace(hour=0, minute=0, second=0)
    end_datetime = target_date.replace(hour=23, minute=59, second=59)
    return start_datetime, end_datetime, target_date

def get_priority_report(sheet_name: Optional[str] = None) -> Optional[Dict[str, pd.DataFrame]]:
    """
    Get priority report data from the API.
    
    Args:
        sheet_name: Name of the sheet to retrieve, or 'all' for all sheets
        
    Returns:
        Dictionary of DataFrames if sheet_name is 'all', otherwise a single DataFrame
    """
    url = "https://wise.logisticsteam.com/v2/valleyview/cp/report-center/report/get-report-file"
    
    payload = {
        "reportService": "priorityReport",
        "reportFunction": "buildPriorityReport"
    }
    
    try:
        print("Fetching priority report file...")
        response = requests.post(url, headers=WISE_API_HEADERS, json=payload)
        response.raise_for_status()
        
        if response.status_code == 200:
            excel_file = io.BytesIO(response.content)
            available_sheets = pd.ExcelFile(excel_file).sheet_names
            print(f"Available sheets: {available_sheets}")
            
            if sheet_name == 'all':
                try:
                    return pd.read_excel(excel_file, sheet_name=['RG Outbound', 'Inbound'])
                except ValueError:
                    print("Standard sheet names not found, trying alternative names...")
                    outbound_sheet = next((s for s in available_sheets if 'outbound' in s.lower()), None)
                    inbound_sheet = next((s for s in available_sheets if 'inbound' in s.lower()), None)
                    
                    if outbound_sheet and inbound_sheet:
                        return pd.read_excel(excel_file, sheet_name=[outbound_sheet, inbound_sheet])
                    else:
                        print("Could not find appropriate sheets in Excel file")
            else:
                target_sheet = sheet_name or 'RG Outbound'
                if target_sheet not in available_sheets:
                    target_sheet = next((s for s in available_sheets 
                                       if ('outbound' if 'outbound' in target_sheet.lower() else 'inbound') in s.lower()), None)
                
                if target_sheet and target_sheet in available_sheets:
                    return pd.read_excel(excel_file, sheet_name=target_sheet)
                else:
                    print(f"Could not find sheet {target_sheet}")
        
        return None
    
    except Exception as e:
        print(f"Error fetching priority report: {str(e)}")
        return None

def get_inbound_receipts() -> List[Dict[str, Any]]:
    """
    Get inbound receipt data from the API.
    
    Returns:
        List of receipt dictionaries
    """
    tomorrow_start, tomorrow_end, _ = get_tomorrow_date_range()
    url = "https://wise.logisticsteam.com/v2/valleyview/bam/inbound/receipt/search-by-paging"
    
    payload = {
        "appointmentTimeFrom": tomorrow_start.strftime('%Y-%m-%dT%H:%M:%S'),
        "appointmentTimeTo": tomorrow_end.strftime('%Y-%m-%dT%H:%M:%S'),
        "customerIds": [DEFAULT_CUSTOMER_ID],
        "paging": {"pageNo": 1, "limit": 100},
        "statuses": ["Appointment Made", "In Yard"]
    }

    try:
        print("Fetching inbound receipts...")
        response = requests.post(url, headers=WISE_API_HEADERS, json=payload)
        response.raise_for_status()
        
        data = response.json()
        receipts = data.get('receipts', [])
        print(f"Retrieved {len(receipts)} inbound receipts")
        
        return receipts
    
    except Exception as e:
        print(f"Error in inbound receipt API: {str(e)}")
        return []

def get_equipment_details() -> List[Dict[str, Any]]:
    """
    Get equipment details from the API.
    
    Returns:
        List of equipment details dictionaries with receipt IDs
    """
    url = "https://wise.logisticsteam.com/v2/valleyview/bam/wms-app/csr/equipmentDetail"
    
    payload = {
        "customerId": DEFAULT_CUSTOMER_ID,
        "type": "Container",
        "equipmentStatus": "Full",
        "statuses": ["Loaded", "Full to Offload"],
        "paging": {"pageNo": 1, "limit": 100}
    }
    
    try:
        print("Fetching equipment details...")
        response = requests.post(url, headers=WISE_API_HEADERS, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, list):
            print(f"Unexpected response format from equipment details API. Expected list, got {type(data)}")
            return []
            
        # Extract equipment details with receipt IDs
        equipment_details = []
        for equipment in data:
            if isinstance(equipment, dict):
                receipt_ids = equipment.get('receiptIds', [])
                if receipt_ids:
                    equipment_details.append({
                        'equipmentNo': equipment.get('equipmentNo', ''),
                        'receiptIds': receipt_ids,
                        'status': equipment.get('status', ''),
                        'location': equipment.get('currentLocation', '')
                    })
                    
        print(f"Processed {len(equipment_details)} equipment details with receipt IDs")
        return equipment_details
    
    except Exception as e:
        print(f"Error in fetching equipment details: {str(e)}")

def get_outbound_orders():
    """
    Get outbound orders from status report.
    
    Returns:
        List of dictionaries containing outbound order information
    """
    tomorrow_start, tomorrow_end, _ = get_tomorrow_date_range()
    url = "https://wise.logisticsteam.com/v2/valleyview/report-center/outbound/order-status-report/search-by-paging"
    
    payload = {
        "statuses": ["Imported", "Open", "Planning", "Planned", "Committed"],
        "customerId": DEFAULT_CUSTOMER_ID,
        "orderTypes": ["Regular Order"],
        "appointmentTimeFrom": tomorrow_start.strftime('%Y-%m-%dT%H:%M:%S'),
        "appointmentTimeTo": tomorrow_end.strftime('%Y-%m-%dT%H:%M:%S'),
        "paging": {"pageNo": 1, "limit": 100}
    }
    
    try:
        response = requests.post(url, headers=WISE_API_HEADERS, json=payload)
        response.raise_for_status()
        
        data = response.json()
        orders = data.get('results', {}).get('data', [])
        
        # Process and standardize order data
        processed_orders = []
        for order in orders:
            try:
                pallet_qty = float(order.get('Pallet QTY', 0)) or 0
                order_qty = float(order.get('Order QTY', 0)) or 0
                picking_type = order.get('Picking Type', '')
            except (ValueError, TypeError):
                pallet_qty = order_qty = 0
                picking_type = ''
                
            processed_orders.append({
                'order_no': order.get('Order No.'),
                'status': order.get('Order Status', 'Unknown'),
                'customer': order.get('Customer ID', 'Unknown'),
                'ship_to': order.get('Ship to', 'Unknown'),
                'state': order.get('State', 'Unknown'),
                'reference_no': order.get('Reference Number', ''),
                'target_completion_date': order.get('Target Completion Date', ''),
                'pallet_qty': pallet_qty,
                'order_qty': order_qty,
                'Picking Type': picking_type
            })
        
        return processed_orders
    
    except Exception as e:
        print(f"Error in outbound status report API: {str(e)}")
        return []

def get_picked_outbound_orders():
    """
    Get picked outbound orders from status report.
    
    Returns:
        List of dictionaries containing picked outbound order information
    """
    tomorrow_start, tomorrow_end, _ = get_tomorrow_date_range()
    url = "https://wise.logisticsteam.com/v2/valleyview/report-center/outbound/order-status-report/search-by-paging"
    
    payload = {
        "statuses": ["Picked"],
        "customerId": DEFAULT_CUSTOMER_ID,
        "orderTypes": ["Regular Order"],
        "appointmentTimeFrom": tomorrow_start.strftime('%Y-%m-%dT%H:%M:%S'),
        "appointmentTimeTo": tomorrow_end.strftime('%Y-%m-%dT%H:%M:%S'),
        "paging": {"pageNo": 1, "limit": 100}
    }
    
    try:
        print("Fetching picked outbound orders...")
        response = requests.post(url, headers=WISE_API_HEADERS, json=payload)
        response.raise_for_status()
        
        data = response.json()
        orders = data.get('results', {}).get('data', [])
        
        # Process and standardize picked order data
        processed_picked_orders = []
        for order in orders:
            try:
                pallet_qty = float(order.get('Pallet QTY', 0)) or 0
                order_qty = float(order.get('Order QTY', 0)) or 0
            except (ValueError, TypeError):
                pallet_qty = order_qty = 0
                
            processed_picked_orders.append({
                'order_no': order.get('Order No.'),
                'status': order.get('Order Status', 'Unknown'),
                'customer': order.get('Customer ID', 'Unknown'),
                'ship_to': order.get('Ship to', 'Unknown'),
                'state': order.get('State', 'Unknown'),
                'reference_no': order.get('Reference Number', ''),
                'target_completion_date': order.get('Target Completion Date', ''),
                'pallet_qty': pallet_qty,
                'order_qty': order_qty
            })
        
        return processed_picked_orders
    
    except Exception as e:
        print(f"Error in picked outbound status report API: {str(e)}")
        return []