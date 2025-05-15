"""Utility functions for the warehouse scheduler."""

import pandas as pd
from typing import Optional, Tuple

def find_column_by_pattern(df: pd.DataFrame, patterns: list) -> Optional[str]:
    """
    Find a column in a DataFrame that matches any of the given patterns.
    
    Args:
        df: DataFrame to search in
        patterns: List of patterns to match
        
    Returns:
        Column name or None if not found
    """
    for col in df.columns:
        col_str = str(col).strip().lower()
        if any(pattern.lower() in col_str for pattern in patterns):
            return col
    return None

def safe_float_convert(value) -> float:
    """
    Safely convert a value to float, returning 0 if conversion fails.
    
    Args:
        value: Value to convert
        
    Returns:
        Converted float value or 0
    """
    try:
        if pd.isna(value):
            return 0
        return float(value)
    except (ValueError, TypeError):
        return 0

def parse_column_data(df: pd.DataFrame, column: str) -> list:
    """
    Parse data from a DataFrame column into a list, handling missing values.
    
    Args:
        df: DataFrame containing the data
        column: Column name to parse
        
    Returns:
        List of parsed values
    """
    if column not in df.columns:
        return []
    
    return [safe_float_convert(val) for val in df[column].values]