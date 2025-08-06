"""Main application for warehouse scheduler."""

import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import schedule_service
from database import save_scheduled_employees, get_scheduled_employees

# Initialize FastAPI app
app = FastAPI(
    title="Warehouse Scheduler API",
    description="API for calculating warehouse staffing requirements",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    try:
        # Run the scheduler
        schedule_result = schedule_service.run_scheduler()
        
        if not schedule_result:
            return {"error": "Failed to generate schedule"}
            
        tomorrow_data, day_after_data = schedule_result
        
        # Save scheduled employees to database for tomorrow
        tomorrow_saved = save_scheduled_employees(
            tomorrow_data['date'],
            tomorrow_data['day_name'],
            tomorrow_data['assigned_employees']
        )
        
        # Save scheduled employees to database for day after tomorrow
        day_after_saved = save_scheduled_employees(
            day_after_data['date'],
            day_after_data['day_name'],
            day_after_data['assigned_employees']
        )
        
        return {
            "message": "Schedule generated successfully",
            "tomorrow": tomorrow_data,
            "day_after": day_after_data,
            "database_saves": {
                "tomorrow_saved": tomorrow_saved,
                "day_after_saved": day_after_saved
            }
        }
        
    except Exception as e:
        print(f"Error in root endpoint: {str(e)}")
        return {"error": str(e)}

@app.get("/api/schedule")
async def get_schedule() -> Dict[str, Any]:
    """
    Get warehouse scheduling data for tomorrow.
    
    Returns:
        Dict containing scheduling data including required staff and forecast.
    
    Raises:
        HTTPException: If there's an error generating the schedule.
    """
    try:
        scheduling_data = schedule_service.run_scheduler()
        if not scheduling_data:
            raise HTTPException(
                status_code=404,
                detail="No scheduling data available for tomorrow"
            )
        
        # Save scheduled employees to database
        tomorrow_data = scheduling_data.get('tomorrow', {})
        day_after_data = scheduling_data.get('day_after', {})
        
        saves_successful = {}
        if tomorrow_data:
            saves_successful['tomorrow'] = save_scheduled_employees(
                tomorrow_data['date'],
                tomorrow_data['day_name'],
                tomorrow_data['assigned_employees']
            )
        
        if day_after_data:
            saves_successful['day_after'] = save_scheduled_employees(
                day_after_data['date'],
                day_after_data['day_name'],
                day_after_data['assigned_employees']
            )
        
        return {
            'success': True,
            'data': scheduling_data,
            'database_saves': saves_successful
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating schedule: {str(e)}"
        )

@app.get("/api/scheduled-employees/{date}")
async def get_scheduled_employees_by_date(date: str) -> Dict[str, Any]:
    """
    Get scheduled employees for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Dict containing scheduled employee details for the specified date.
    
    Raises:
        HTTPException: If there's an error retrieving the scheduled employees.
    """
    try:
        scheduled_data = get_scheduled_employees(date)
        
        return {
            'success': True,
            'data': scheduled_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving scheduled employees: {str(e)}"
        )

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting API server on port {port}")
        print(f"API documentation available at:")
        print(f"  - http://localhost:{port}/docs")
        print(f"  - http://localhost:{port}/redoc")
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    else:
        print("\n=== Warehouse Shift Scheduler ===")
        result = schedule_service.run_scheduler()
        if result:
            # Process tomorrow's data
            tomorrow_data = result['tomorrow']
            print(f"\nScheduling for Tomorrow ({tomorrow_data['date']} - {tomorrow_data['day_name']})")
            print("\nForecast:")
            print(f"- Shipping Pallets: {tomorrow_data['forecast_data']['shipping_pallets']:.1f}")
            print(f"- Incoming Pallets: {tomorrow_data['forecast_data']['incoming_pallets']:.1f}")
            print(f"- Cases to Pick: {tomorrow_data['forecast_data']['cases_to_pick']:.1f}")
            print(f"- Staged Pallets: {tomorrow_data['forecast_data']['staged_pallets']:.1f}")
            
            print("\nRequired Staff:")
            for role, count in tomorrow_data['required_roles'].items():
                print(f"- {role}: {count}")

            # Process day after tomorrow's data
            day_after_data = result['day_after']
            print(f"\nScheduling for Day After Tomorrow ({day_after_data['date']} - {day_after_data['day_name']})")
            print("\nForecast:")
            print(f"- Shipping Pallets: {day_after_data['forecast_data']['shipping_pallets']:.1f}")
            print(f"- Incoming Pallets: {day_after_data['forecast_data']['incoming_pallets']:.1f}")
            print(f"- Cases to Pick: {day_after_data['forecast_data']['cases_to_pick']:.1f}")
            print(f"- Staged Pallets: {day_after_data['forecast_data']['staged_pallets']:.1f}")
            
            print("\nRequired Staff:")
            for role, count in day_after_data['required_roles'].items():
                print(f"- {role}: {count}")
        else:
            print("\nNo scheduling data available for the next two days")