"""Data models for the warehouse scheduler."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, date

class Employee(BaseModel):
    """Employee model."""
    id: str
    name: str
    email: Optional[str] = None
    active: bool = True
    on_leave: bool = False
    skills: List[str] = []
    shift_preferences: List[str] = []
    name_variations: List[str] = []

class InboundReceipt(BaseModel):
    """Inbound receipt model."""
    rn: str
    status: str = "Unknown"
    customer: str = "Unknown"
    appointment_time: Optional[datetime] = None
    pallet_count: float = 0
    priority_pallet_count: float = 0

class OutboundOrder(BaseModel):
    """Outbound order model."""
    dn: str
    status: str = "Unknown"
    customer: str = "Unknown"
    ship_to: str = "Unknown"
    state: str = "Unknown"
    reference_no: str = ""
    target_completion_date: Optional[datetime] = None
    pallet_count: float = 0
    order_qty: float = 0

class ForecastData(BaseModel):
    """Forecast data model."""
    daily_shipping_pallets: List[float]
    daily_incoming_pallets: List[float]
    daily_order_qty: List[float]

class ShiftSchedule(BaseModel):
    """Shift schedule model."""
    date: date
    day_name: str
    start_time: str
    end_time: str
    location: str
    lunch_duration: str

class ScheduleData(BaseModel):
    """Schedule data model."""
    date: str
    day_name: str
    required_roles: Dict[str, int]
    assigned_employees: Dict[str, List[str]]
    forecast_data: Dict[str, float]