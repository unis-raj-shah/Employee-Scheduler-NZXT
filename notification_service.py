"""Service for sending notifications and emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any
from config import EMAIL_CONFIG, DEFAULT_SHIFT
from database import get_employee_details
from metrics_config import ROLE_URLS, DEFAULT_ROLE_URL

def create_schedule_email_html(schedule_data: Dict[str, Any], 
                              employee_name: str, 
                              employee_email: str, 
                              role: str) -> str:
    """
    Create HTML content for schedule email.
    
    Args:
        schedule_data: Schedule data dictionary
        employee_name: Name of the employee
        employee_email: Email of the employee
        role: Role assigned to the employee
        
    Returns:
        HTML content for the email
    """
    # Convert schedule date string to datetime object
    schedule_date = datetime.strptime(schedule_data['date'], '%Y-%m-%d')
    # Get Monday of the week
    monday = schedule_date - timedelta(days=schedule_date.weekday())
    
    # Format the role nicely
    formatted_role = role.replace('_', ' ').title()
    
    # Base URL for the employee portal
    portal_base = "https://access.paylocity.com/"
    
    # Create enhanced HTML content with the template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Shift Schedule</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                margin: 0;
                padding: 0;
                background-color: #f9f9f9;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                padding: 20px 0;
                border-bottom: 2px solid #4CAF50;
            }}
            .header h1 {{
                color: #4CAF50;
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 20px 0;
            }}
            .schedule {{
                background-color: #f1f8e9;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .schedule h2 {{
                margin-top: 0;
                color: #2E7D32;
            }}
            .schedule-details {{
                padding: 10px;
                background-color: #ffffff;
                border-radius: 5px;
                border-left: 4px solid #4CAF50;
                margin-bottom: 15px;
            }}
            .table-container {{
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                margin-bottom: 15px;
                border-radius: 4px;
                position: relative;
                scrollbar-width: thin;
                scrollbar-color: #4CAF50 #f1f1f1;
                -ms-overflow-style: -ms-autohiding-scrollbar;
                scroll-behavior: smooth;
                will-change: scroll-position;
                -webkit-transform: translateZ(0);
                -moz-transform: translateZ(0);
                transform: translateZ(0);
                -webkit-backface-visibility: hidden;
                -moz-backface-visibility: hidden;
                backface-visibility: hidden;
                perspective: 1000;
                overflow-scrolling: touch;
                -webkit-scroll-snap-type: x mandatory;
                scroll-snap-type: x mandatory;
                scroll-snap-points-x: repeat(100%);
                -webkit-overflow-scrolling: touch;
                overscroll-behavior-x: contain;
            }}
            
            /* Smooth scrolling for modern browsers */
            @media (prefers-reduced-motion: no-preference) {{
                .table-container {{
                    scroll-behavior: smooth;
                }}
            }}
            
            /* Custom scrollbar styling */
            .table-container::-webkit-scrollbar {{
                height: 8px;
            }}
            
            .table-container::-webkit-scrollbar-track {{
                background: #f1f1f1;
                border-radius: 4px;
            }}
            
            .table-container::-webkit-scrollbar-thumb {{
                background: #4CAF50;
                border-radius: 4px;
            }}
            
            .table-container::-webkit-scrollbar-thumb:hover {{
                background: #45a049;
            }}
            
            .schedule-table {{
                width: 100%;
                min-width: 500px;
                border-collapse: collapse;
                margin: 10px 0;
                background: #fff;
                transform: translate3d(0, 0, 0);
                -webkit-transform: translate3d(0, 0, 0);
                -webkit-backface-visibility: hidden;
                -moz-backface-visibility: hidden;
                backface-visibility: hidden;
                perspective: 1000;
            }}
            
            .schedule-table th,
            .schedule-table td {{
                padding: 8px;
                text-align: left;
                border: 1px solid #ddd;
                white-space: nowrap;
            }}
            .schedule-table th {{
                background-color: #4CAF50;
                color: white;
            }}
            .schedule-table tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            @media screen and (max-width: 600px) {{
                .container {{
                    padding: 10px;
                }}
                .schedule {{
                    padding: 10px;
                }}
                .schedule-details {{
                    padding: 5px;
                }}
                .schedule-table th,
                .schedule-table td {{
                    padding: 6px;
                    font-size: 14px;
                }}
                .table-container::before,
                .table-container::after {{
                    content: '';
                    position: absolute;
                    top: 0;
                    bottom: 0;
                    width: 5px;
                    pointer-events: none;
                    transition: opacity 0.3s ease;
                }}
                
                .table-container::before {{
                    left: 0;
                    background: linear-gradient(to right, rgba(0,0,0,0.05), transparent);
                }}
                
                .table-container::after {{
                    right: 0;
                    background: linear-gradient(to left, rgba(0,0,0,0.05), transparent);
                }}
            }}
            .menu-section {{
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f5f5f5;
                border-radius: 5px;
            }}
            .menu-section h2 {{
                color: #1976D2;
                margin-top: 0;
            }}
            .menu-item {{
                display: block;
                padding: 8px 0;
                color: #1976D2;
                text-decoration: none;
                transition: color 0.3s;
            }}
            .menu-item:hover {{
                color: #0D47A1;
            }}
            .footer {{
                text-align: center;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #757575;
                font-size: 12px;
            }}
            .staff-section h2 {{
                margin-top: 0;
                color: #1976D2;
            }}
            .operation-section {{
                background-color: #ffffff;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
                border-left: 4px solid #1976D2;
            }}
            .operation-section h3 {{
                color: #1976D2;
                margin-top: 0;
                margin-bottom: 10px;
                font-size: 16px;
            }}
            .operation-section p {{
                margin: 5px 0;
            }}
            .role-list {{
                padding-left: 20px;
            }}
            .role-list ul {{
                list-style-type: none;
                padding-left: 20px;
                margin: 0;
            }}
            .role-list li {{
                margin: 8px 0;
                position: relative;
            }}
            .role-list li strong {{
                display: inline-block;
                min-width: 200px;
            }}
            .total-section {{
                background-color: #e8f5e9;
                border-left: 4px solid #2E7D32;
                margin-top: 20px;
            }}
            .total-section h3 {{
                color: #2E7D32;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Your Shift Schedule + Quick Actions</h1>
            </div>
            
            <div class="content">
                <p>Hello {employee_name},</p>
                <p>You have been scheduled to work on <strong>{schedule_data['date']} ({schedule_data['day_name']})</strong>.</p>
                
                <div class="schedule">
                    <h2>Your Schedule Details:</h2>
                    <div class="schedule-details">
                        <div class="table-container">
                            <table class="schedule-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Role</th>
                                        <th>Location</th>
                                        <th>Hours</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>{schedule_data['date']} ({schedule_data['day_name']})</strong></td>
                                        <td><a href="{get_role_url(role)}">{formatted_role}</a></td>
                                        <td>{DEFAULT_SHIFT['location']}</td>
                                        <td>{DEFAULT_SHIFT['start_time']} - {DEFAULT_SHIFT['end_time']}<br><small>Includes Lunch: {DEFAULT_SHIFT['lunch_duration']}</small></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <h2>Weekly Schedule</h2>
                    <div class="schedule-details">
                        <div class="table-container">
                            <table class="schedule-table">
                                <thead>
                                    <tr>
                                        <th>Day</th>
                                        <th>Location</th>
                                        <th>Hours</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>{monday.strftime('%A, %B %d')}</strong></td>
                                        <td>{DEFAULT_SHIFT['location']}</td>
                                        <td>{DEFAULT_SHIFT['start_time']} - {DEFAULT_SHIFT['end_time']}<br><small>Includes Lunch: {DEFAULT_SHIFT['lunch_duration']}</small></td>
                                    </tr>
                                    <tr>
                                        <td><strong>{(monday + timedelta(days=1)).strftime('%A, %B %d')}</strong></td>
                                        <td>{DEFAULT_SHIFT['location']}</td>
                                        <td>{DEFAULT_SHIFT['start_time']} - {DEFAULT_SHIFT['end_time']}<br><small>Includes Lunch: {DEFAULT_SHIFT['lunch_duration']}</small></td>
                                    </tr>
                                    <tr>
                                        <td><strong>{(monday + timedelta(days=2)).strftime('%A, %B %d')}</strong></td>
                                        <td>{DEFAULT_SHIFT['location']}</td>
                                        <td>{DEFAULT_SHIFT['start_time']} - {DEFAULT_SHIFT['end_time']}<br><small>Includes Lunch: {DEFAULT_SHIFT['lunch_duration']}</small></td>
                                    </tr>
                                    <tr>
                                        <td><strong>{(monday + timedelta(days=3)).strftime('%A, %B %d')}</strong></td>
                                        <td>{DEFAULT_SHIFT['location']}</td>
                                        <td>{DEFAULT_SHIFT['start_time']} - {DEFAULT_SHIFT['end_time']}<br><small>Includes Lunch: {DEFAULT_SHIFT['lunch_duration']}</small></td>
                                    </tr>
                                    <tr>
                                        <td><strong>{(monday + timedelta(days=4)).strftime('%A, %B %d')}</strong></td>
                                        <td>{DEFAULT_SHIFT['location']}</td>
                                        <td>{DEFAULT_SHIFT['start_time']} - {DEFAULT_SHIFT['end_time']}<br><small>Includes Lunch: {DEFAULT_SHIFT['lunch_duration']}</small></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <p style="margin-top: 15px;"><strong>Total Hours:</strong> 40 hours/week</p>
                    </div>
                </div>

                <div class="menu-section">
                    <h2>Schedule & Team</h2>
                    <a href="{portal_base}/schedule/team" class="menu-item">→ View Team Schedule</a>
                    <a href="{portal_base}/team/contact" class="menu-item">→ Contact Teammate</a>
                </div>

                <div class="menu-section">
                    <h2>Shift Management</h2>
                    <a href="{portal_base}/shifts/swap" class="menu-item">→ Swap Your Shift</a>
                    <a href="{portal_base}/shifts/pickup" class="menu-item">→ Pick Up Open Shifts</a>
                    <a href="{portal_base}/shifts/drop" class="menu-item">→ Drop a Shift</a>
                </div>

                <div class="menu-section">
                    <h2>Availability & PTO</h2>
                    <a href="{portal_base}/availability/update" class="menu-item">→ Update Availability</a>
                    <a href="{portal_base}/pto/request" class="menu-item">→ Request Time Off</a>
                    <a href="{portal_base}/pto/balance" class="menu-item">→ View PTO Balance</a>
                </div>

                <div class="menu-section">
                    <h2>Clock Functions</h2>
                    <a href="{portal_base}/clock/punch" class="menu-item">→ Clock In/Out</a>
                    <a href="{portal_base}/timesheet/history" class="menu-item">→ Timesheet History</a>
                </div>

                <div class="menu-section">
                    <h2>Calendar & Reminders</h2>
                    <a href="{portal_base}/calendar/google-sync" class="menu-item">→ Sync to Google Calendar</a>
                    <a href="{portal_base}/calendar/outlook-sync" class="menu-item">→ Sync to Outlook/iCal</a>
                    <a href="{portal_base}/notifications/settings" class="menu-item">→ Set Shift Reminders via SMS or Email</a>
                </div>

                <div class="menu-section">
                    <h2>Support</h2>
                    <a href="{portal_base}/support/manager" class="menu-item">→ Contact Manager</a>
                    <a href="{portal_base}/support/portal" class="menu-item">→ Employee Support Portal</a>
                </div>
                
                <p>If you have any questions or concerns about your schedule, please contact your supervisor immediately.</p>
                
                <p>Thank you for your dedication to our team!</p>
                
                <p>Best regards,<br>Warehouse Management</p>
            </div>
            
            <div class="footer">
                <p>This email was sent to {employee_email}. If you have questions about this schedule or are unable to work your assigned shift, please contact your supervisor immediately.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_schedule_email(schedule_data: Dict[str, Any], assigned_employees: Dict[str, List[str]]) -> bool:
    """
    Send individual schedule emails to assigned employees.
    
    Args:
        schedule_data: Dictionary containing the scheduling results
        assigned_employees: Dictionary mapping roles to lists of assigned employee IDs
        
    Returns:
        Boolean indicating success
    """
    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["sender_password"]:
        print("Email configuration not set up.")
        return False

    try:
        for role, employees in assigned_employees.items():
            # Extract base role without operation prefix for display
            display_role = role.split('_', 1)[-1] if '_' in role else role
            
            for emp_id in employees:
                try:
                    # Get employee email from database
                    metadata = get_employee_details(emp_id)
                    if not metadata:
                        print(f"No data found for employee {emp_id}")
                        continue
                    
                    email = metadata.get("email")
                    name = metadata.get("name", emp_id)
                    
                    if not email:
                        print(f"No email found for employee {emp_id}")
                        continue
                    
                    # Create email message
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = f"Your Shift Schedule for {schedule_data['date']} + Quick Actions"
                    msg["From"] = EMAIL_CONFIG["sender_email"]
                    msg["To"] = email
                    
                    # Create the HTML content
                    html = create_schedule_email_html(schedule_data, name, email, display_role)
                    msg.attach(MIMEText(html, "html"))
                    
                    # Send email
                    with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                        server.starttls()
                        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
                        server.send_message(msg)
                    
                    print(f"Enhanced schedule email sent successfully to {email}")
                
                except Exception as e:
                    print(f"Error sending email to employee {emp_id}: {str(e)}")
                    continue
        
        return True
    
    except Exception as e:
        print(f"Error in send_schedule_email: {str(e)}")
        return False

def send_forecast_email(forecast_data: Dict[str, Any], required_staff: Dict[str, int]) -> bool:
    """
    Send forecast email to the team.
    
    Args:
        forecast_data: Dictionary containing forecast data
        required_staff: Dictionary containing required staff counts
        
    Returns:
        Boolean indicating success
    """
    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["sender_password"]:
        print("Email configuration not set up.")
        return False

    try:
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Forecast for Tomorrow for NZXT"
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = ", ".join(EMAIL_CONFIG["default_recipients"])
        
        # Create the HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Forecast</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                    margin: 0;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    padding: 20px 0;
                    border-bottom: 2px solid #4CAF50;
                }}
                .header h1 {{
                    color: #4CAF50;
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px 0;
                }}
                .forecast-section {{
                    background-color: #f1f8e9;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .forecast-section h2 {{
                    margin-top: 0;
                    color: #2E7D32;
                }}
                .staff-section {{
                    background-color: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .staff-section h2 {{
                    margin-top: 0;
                    color: #1976D2;
                }}
                .footer {{
                    text-align: center;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    color: #757575;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Forecast for Tomorrow</h1>
                </div>
                
                <div class="content">
                    <div class="forecast-section">
                        <h2>Forecast:</h2>
                        <p><strong>Shipping Pallets:</strong> {forecast_data.get('shipping_pallets', 0):.1f}</p>
                        <p><strong>Receiving Pallets:</strong> {forecast_data.get('incoming_pallets', 0):.1f}</p>
                        <p><strong>Cases to Pick:</strong> {forecast_data.get('cases_to_pick', 0):,.0f}</p>
                        <p><strong>Staged Pallets:</strong> {forecast_data.get('picked_pallets', 0):.1f}</p>
                    </div>

                    <div class="staff-section">
                        <h2>Required Staff:</h2>
                        <div class="operation-section">
                            <h3>Receiving Operations:</h3>
                            <div class="role-list">
                                <ul>
                                    <li><strong>Forklift Drivers:</strong> {required_staff.get('inbound', {}).get('forklift_driver', 0)}</li>
                                    <li><strong>Receivers:</strong> {required_staff.get('inbound', {}).get('receiver', 0)}</li>
                                    <li><strong>Lumpers:</strong> {required_staff.get('inbound', {}).get('lumper', 0)}</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="operation-section">
                            <h3>Picking Operations:</h3>
                            <div class="role-list">
                                <ul>
                                    <li><strong>Forklift Drivers:</strong> {required_staff.get('picking', {}).get('forklift_driver', 0)}</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="operation-section">
                            <h3>Loading Operations:</h3>
                            <div class="role-list">
                                <ul>
                                    <li><strong>Forklift Drivers:</strong> {required_staff.get('loading', {}).get('forklift_driver', 0)}</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="operation-section">
                            <h3>Replenishment:</h3>
                            <div class="role-list">
                                <ul>
                                    <li><strong>Staff:</strong> {required_staff.get('replenishment', {}).get('staff', 0)}</li>
                                </ul>
                            </div>
                        </div>

                        <div class="operation-section total-section">
                            <h3>Total Headcount:</h3>
                            <p><strong>Total Staff Required:</strong> {
                                required_staff.get('inbound', {}).get('forklift_driver', 0) +
                                required_staff.get('inbound', {}).get('receiver', 0) +
                                required_staff.get('inbound', {}).get('lumper', 0) +
                                required_staff.get('picking', {}).get('forklift_driver', 0) +
                                required_staff.get('loading', {}).get('forklift_driver', 0) +
                                required_staff.get('replenishment', {}).get('staff', 0)
                            }</p>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated forecast email. Please contact the warehouse manager if you have any questions.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, "html"))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)
        
        print("Forecast email sent successfully")
        return True
    
    except Exception as e:
        print(f"Error sending forecast email: {str(e)}")
        return False

def get_role_url(role: str) -> str:
    """
    Get the URL associated with a specific role.
    
    Args:
        role: The role name
        
    Returns:
        URL string for the role
    """
    # Convert role to lowercase and replace spaces with underscores for consistent matching
    normalized_role = role.lower().replace(' ', '_')
    
    # Return the URL if found, otherwise return the default URL
    return ROLE_URLS.get(normalized_role, DEFAULT_ROLE_URL)

def send_short_staffed_notification(shortages: Dict[str, int], date: str) -> bool:
    """
    Send a notification email to managers about short-staffed roles.
    
    Args:
        shortages: Dictionary of roles and their shortfall counts
        date: The date for which the shortage applies
        
    Returns:
        Boolean indicating success
    """
    if not shortages:
        print("No shortages to notify.")
        return False

    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["sender_password"]:
        print("Email configuration not set up.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Short Staffed Alert for {date}"
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = ", ".join(EMAIL_CONFIG["default_recipients"])

        # Create the HTML content
        html = f"""
        <html>
        <body>
            <h2>Short Staffed Alert for {date}</h2>
            <p>The following roles are short staffed:</p>
            <ul>
                {''.join(f'<li><strong>{role}:</strong> {count}</li>' for role, count in shortages.items())}
            </ul>
            <p>Please review and take necessary action.</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)

        print("Short staffed notification sent to managers.")
        return True

    except Exception as e:
        print(f"Error sending short staffed notification: {str(e)}")
        return False