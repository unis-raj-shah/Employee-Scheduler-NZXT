"""Module for tracking staffing history and calculating moving averages."""

from datetime import datetime, timedelta
import chromadb
from typing import Dict, List, Any
import json
from config import DB_PATH

# Initialize ChromaDB client for staffing history
chroma_client = chromadb.PersistentClient(path=DB_PATH)
staffing_collection = chroma_client.get_or_create_collection(name="staffing_history")

def save_daily_staffing(date: str, required_roles: Dict[str, Any]) -> bool:
    """
    Save daily staffing requirements to the database.
    
    Args:
        date: Date string in YYYY-MM-DD format
        required_roles: Dictionary of required roles and their counts
        
    Returns:
        Boolean indicating success
    """
    try:
        # Flatten the nested role structure
        flattened_roles = {}
        for operation, roles in required_roles.items():
            for role, count in roles.items():
                role_key = f"{operation}_{role}"
                flattened_roles[role_key] = count
        
        # Create metadata and document
        metadata = {
            "date": date,
            "roles": json.dumps(flattened_roles)  # Convert dictionary to JSON string
        }
        
        document = f"Staffing requirements for {date}: {flattened_roles}"
        
        # Save to ChromaDB
        staffing_collection.upsert(
            ids=[date],
            metadatas=[metadata],
            documents=[document]
        )
        
        return True
        
    except Exception as e:
        print(f"Error saving daily staffing: {str(e)}")
        return False

def get_staffing_history(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get staffing history for the specified number of days.
    
    Args:
        days: Number of days of history to retrieve
        
    Returns:
        List of staffing data dictionaries
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        
        # Get all records
        all_records = staffing_collection.get()
        if not all_records or not all_records["metadatas"]:
            return []
        
        # Filter records within date range
        filtered_records = []
        for i, metadata in enumerate(all_records["metadatas"]):
            record_date = datetime.strptime(metadata["date"], "%Y-%m-%d")
            if start_date <= record_date <= end_date:
                # Parse the JSON string back to dictionary
                roles = json.loads(metadata["roles"])
                filtered_records.append({
                    "date": metadata["date"],
                    "roles": roles
                })
        
        return sorted(filtered_records, key=lambda x: x["date"])
        
    except Exception as e:
        print(f"Error getting staffing history: {str(e)}")
        return []

def calculate_moving_averages(days: int = 7) -> Dict[str, float]:
    """
    Calculate moving averages for each role over the specified period.
    
    Args:
        days: Number of days to include in the moving average
        
    Returns:
        Dictionary of role moving averages
    """
    try:
        history = get_staffing_history(days)
        if not history:
            return {}
        
        # Initialize role totals
        role_totals = {}
        role_counts = {}
        
        # Sum up role counts
        for record in history:
            for role, count in record["roles"].items():
                if role not in role_totals:
                    role_totals[role] = 0
                    role_counts[role] = 0
                role_totals[role] += count
                role_counts[role] += 1
        
        # Calculate averages
        moving_averages = {}
        for role in role_totals:
            if role_counts[role] > 0:
                moving_averages[role] = round(role_totals[role] / role_counts[role], 1)
        
        return moving_averages
        
    except Exception as e:
        print(f"Error calculating moving averages: {str(e)}")
        return {} 