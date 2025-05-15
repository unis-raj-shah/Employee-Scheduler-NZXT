"""Database connection and operations for the warehouse scheduler."""

import chromadb
import json
import re
import Levenshtein
from typing import Dict, List, Any, Optional
from config import DB_PATH, ROLE_MAPPINGS

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=DB_PATH)
employee_collection = chroma_client.get_or_create_collection(name="employees")

def normalize_role(role: str) -> str:
    """
    Normalize role names for consistent matching.
    
    Args:
        role: Role name to normalize
        
    Returns:
        Normalized role name
    """
    role = role.lower().strip()
    # Remove trailing 's' if present (e.g., "drivers" -> "driver")
    role = re.sub(r's$', '', role)  
    # Replace spaces with underscores for consistency
    role = re.sub(r'\s+', '_', role)
    return role

def retrieve_employees(required_roles: Dict[str, int]) -> Dict[str, List[str]]:
    """
    Retrieves employees from ChromaDB matching the required roles.
    
    Args:
        required_roles: Dictionary of roles and their required counts
        
    Returns:
        Dictionary mapping roles to lists of available employee IDs
    """
    matched_employees = {}
    assigned_employees = set()  # Keep track of already assigned employees
    
    try:
        # Get all employees from the database once
        all_employees = employee_collection.get()
        all_ids = all_employees.get("ids", [])
        all_metadatas = all_employees.get("metadatas", [])
        
        # First pass: collect all available employees for each base role
        available_by_role = {}
        for i, metadata in enumerate(all_metadatas):
            if is_employee_available(metadata):
                job_title = normalize_role(metadata.get("original_job_title", ""))
                emp_id = all_ids[i]
                
                # Check each base role
                for role_key in required_roles:
                    base_role = role_key.split('_', 1)[-1] if '_' in role_key else role_key
                    role_variations = ROLE_MAPPINGS.get(base_role, [base_role])
                    
                    if any(variation.lower() in job_title for variation in role_variations):
                        if base_role not in available_by_role:
                            available_by_role[base_role] = []
                        available_by_role[base_role].append(emp_id)
        
        # Second pass: assign employees to roles, ensuring no duplicates
        for role_key in required_roles:
            matched_employees[role_key] = []
            base_role = role_key.split('_', 1)[-1] if '_' in role_key else role_key
            required_count = required_roles[role_key]
            
            # Get available employees for this base role
            available = available_by_role.get(base_role, [])
            
            # Assign employees that haven't been assigned yet
            for emp_id in available:
                if emp_id not in assigned_employees and len(matched_employees[role_key]) < required_count:
                    matched_employees[role_key].append(emp_id)
                    assigned_employees.add(emp_id)
                    print(f"Assigned employee {emp_id} to {role_key}")
            
            # Print warning if not enough employees
            if len(matched_employees[role_key]) < required_count:
                print(f"Warning: Not enough employees for {role_key}. Need {required_count}, found {len(matched_employees[role_key])}")
    
    except Exception as e:
        print(f"Error retrieving employees: {e}")
    
    return matched_employees

def is_employee_available(metadata: Dict[str, Any]) -> bool:
    """
    Check if an employee is available for scheduling based on their metadata.
    
    Args:
        metadata: Employee metadata from ChromaDB
        
    Returns:
        bool: True if employee is available, False otherwise
    """
    try:
        # Check if employee is active
        if not metadata.get("active", True):
            return False
        
        # Check if employee is on leave
        if metadata.get("on_leave", False):
            return False
        
        # Check shift preferences if available
        shift_preferences = metadata.get("shift_preferences", [])
        if shift_preferences and "day" not in shift_preferences:
            return False
        
        return True
        
    except Exception:
        return False

def find_best_match(name: str, employee_list: List[str]) -> Optional[str]:
    """
    Find the best matching employee name using fuzzy matching.
    
    Args:
        name: Name to search for
        employee_list: List of employee IDs to search within
        
    Returns:
        Best matching employee ID or None if no good match found
    """
    best_match = None
    best_score = float('inf')  # Lower is better for Levenshtein distance
    
    name_lower = name.lower()
    
    for emp_id in employee_list:
        # Get name variations
        try:
            emp_data = employee_collection.get(ids=[emp_id])
            if not emp_data or not emp_data["metadatas"]:
                continue
            
            metadata = emp_data["metadatas"][0]
            name_variations_json = metadata.get("name_variations", "[]")
            name_variations = json.loads(name_variations_json)
            
            # If no variations stored, use the ID
            if not name_variations:
                name_variations = [emp_id]
            
            # Try all variations and find the best match
            for variation in name_variations:
                variation_lower = variation.lower()
                
                # Exact match
                if name_lower == variation_lower:
                    return emp_id
                
                # Calculate Levenshtein distance
                distance = Levenshtein.distance(name_lower, variation_lower)
                if distance < best_score:
                    best_score = distance
                    best_match = emp_id
        except Exception as e:
            print(f"Error in name matching for {emp_id}: {e}")
    
    # Only return a match if the score is below a threshold (30% of name length)
    if best_score <= len(name) * 0.3:
        return best_match
    return None

def get_employee_details(emp_id: str) -> Dict[str, Any]:
    """
    Get employee details from the database.
    
    Args:
        emp_id: Employee ID
        
    Returns:
        Dictionary containing employee details
    """
    try:
        emp_data = employee_collection.get(ids=[emp_id])
        if not emp_data or not emp_data["metadatas"]:
            return {}
        
        return emp_data["metadatas"][0]
    except Exception as e:
        print(f"Error getting employee details: {e}")
        return {}