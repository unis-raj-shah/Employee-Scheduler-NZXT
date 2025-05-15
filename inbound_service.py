"""Service for processing inbound warehouse operations."""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from api_client import get_priority_report, get_inbound_receipts, get_equipment_details

def find_priority_report_columns(priority_df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Find relevant columns in inbound priority report.
    
    Args:
        priority_df: Priority report DataFrame
        
    Returns:
        Tuple of column names (pallet_qty, order_qty)
    """
    pallet_qty_col = next((col for col in priority_df.columns 
                          if str(col).strip() == 'Pallet QTY'), None)
    order_qty_col = next((col for col in priority_df.columns 
                       if 'order' in str(col).strip().lower() 
                       and 'qty' in str(col).strip().lower()), None)
    return pallet_qty_col, order_qty_col

def get_matching_incoming_rns(receipts: List[Dict[str, Any]], priority_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Match RNs between incoming receipts and priority report.
    
    Args:
        receipts: List of receipt dictionaries
        priority_df: Priority report DataFrame
        
    Returns:
        List of matched receipt dictionaries with priority data
    """
    if not receipts or priority_df is None or priority_df.empty:
        return []
        
    pallet_qty_col, _ = find_priority_report_columns(priority_df)
    if not pallet_qty_col:
        return []
    
    receipt_rns = {
        receipt.get("id"): {
            "rn": receipt.get("id"),
            "status": receipt.get("status", "Unknown"),
            "customer": receipt.get("customerName", "Unknown"),
            "appointmentTime": receipt.get("appointmentTime", "Unknown"),
            "palletCount": receipt.get("palletCount", 0)
        } if isinstance(receipt, dict) else {
            "rn": receipt,
            "status": "Unknown",
            "customer": "Unknown",
            "appointmentTime": "Unknown",
            "palletCount": 0
        }
        for receipt in receipts if receipt
    }
    
    rn_column = next((col for col in priority_df.columns 
                    if any(possible in str(col).strip() 
                          for possible in ['RN', 'Receipt Number', 'ReceiptNumber', 'Receipt#'])
                    or 'RN' in str(col).strip() 
                    or 'Receipt' in str(col).strip()), None)
    
    if not rn_column:
        return []
        
    priority_data = {}
    for _, row in priority_df.iterrows():
        rn_value = row[rn_column]
        if pd.notna(rn_value):
            rn = str(rn_value).strip()
            rn = f"RN-{rn}" if not rn.startswith('RN-') and rn.isdigit() else rn
            
            if pallet_qty_col and pallet_qty_col in row.index:
                pallet_qty = row[pallet_qty_col]
                if pd.notna(pallet_qty):
                    try:
                        priority_data[rn] = {'pallet_count': float(pallet_qty)}
                    except (ValueError, TypeError):
                        priority_data[rn] = {'pallet_count': 0}
    
    return [
        {**receipt_rns[rn], 'priority_pallet_count': quantities.get('pallet_count', 0)}
        for rn, quantities in priority_data.items()
        if rn in receipt_rns
    ]

def get_equipment_details_pallets(priority_df: pd.DataFrame) -> float:
    """
    Calculate the total pallets from equipment details.
    
    Args:
        priority_df: Priority report DataFrame
        
    Returns:
        Total pallet count
    """
    equipment_details = get_equipment_details()
    
    if not equipment_details:
        return 0

    api_receipt_numbers = []
    for detail in equipment_details:
        receipt_id = detail.get('Receipt #') or detail.get('Reciept #')
        if receipt_id:
            receipt_id = f"RN-{receipt_id}" if not str(receipt_id).startswith('RN-') else str(receipt_id)
            api_receipt_numbers.append(receipt_id)

    if not api_receipt_numbers:
        return 0

    rn_column = next((col for col in priority_df.columns 
                     if any(possible in str(col).strip() 
                           for possible in ['RN', 'Receipt Number', 'ReceiptNumber', 'Receipt#'])), None)
    
    if not rn_column:
        return 0

    pallet_qty_col, _ = find_priority_report_columns(priority_df)
    if not pallet_qty_col:
        return 0

    total_pallets = 0
    for _, row in priority_df.iterrows():
        rn_value = str(row[rn_column]).strip()
        rn_value = f"RN-{rn_value}" if not rn_value.startswith('RN-') else rn_value
        
        if rn_value in set(api_receipt_numbers):
            try:
                pallet_qty = float(row[pallet_qty_col]) if pd.notna(row[pallet_qty_col]) else 0
                total_pallets += pallet_qty
            except (ValueError, TypeError):
                continue

    return total_pallets

def get_incoming_data() -> Dict[str, float]:
    """
    Get inbound receipt data for forecasting.
    
    Returns:
        Dictionary with incoming pallet count
    """
    try:
        priority_dfs = get_priority_report(sheet_name='all')
        if priority_dfs is None or 'Inbound' not in priority_dfs:
            return {"incoming_pallets": 0}
            
        priority_df = priority_dfs['Inbound']
        receipts = get_inbound_receipts()
        
        # Get matched receipts with their pallet counts
        matched_incoming = get_matching_incoming_rns(receipts, priority_df)
        
        receipt_pallets = {}
        for rn in matched_incoming:
            rn_id = rn.get('rn')
            pallet_count = rn.get('priority_pallet_count', 0)
            if isinstance(pallet_count, (int, float, str)) and str(pallet_count).replace('.', '').isdigit():
                # Cap pallet count at 28 if it exceeds 33
                pallet_count = float(pallet_count)
                if pallet_count > 33:
                    pallet_count = 28
                receipt_pallets[rn_id] = pallet_count
        
        equipment_details = get_equipment_details()
        
        # Get equipment receipt numbers and their pallet counts
        equipment_pallets = 0
        if equipment_details:
            # Find pallet count column in priority report
            pallet_qty_col, _ = find_priority_report_columns(priority_df)
            if pallet_qty_col:
                # Get equipment receipt numbers
                equipment_receipts = set()
                for detail in equipment_details:
                    receipt_ids = detail.get('receiptIds', [])
                    for receipt_id in receipt_ids:
                        if receipt_id:
                            equipment_receipts.add(receipt_id)
                
                # Get pallet counts for equipment receipts from priority report
                for _, row in priority_df.iterrows():
                    rn_value = str(row.get('RN', '')).strip()
                    rn_value = f"RN-{rn_value}" if not rn_value.startswith('RN-') else rn_value
                    
                    if rn_value in equipment_receipts and pallet_qty_col in row.index:
                        try:
                            pallet_qty = float(row[pallet_qty_col]) if pd.notna(row[pallet_qty_col]) else 0
                            # Cap pallet count at 28 if it exceeds 33
                            if pallet_qty > 33:
                                pallet_qty = 28
                            equipment_pallets += pallet_qty
                        except (ValueError, TypeError):
                            continue
        
        # Calculate total pallets by combining both sources
        total_pallets = sum(receipt_pallets.values()) + equipment_pallets
        
        return {"incoming_pallets": total_pallets or 0}

    except Exception as e:
        print(f"Error in inbound receipt API: {str(e)}")
        return {"incoming_pallets": 0}