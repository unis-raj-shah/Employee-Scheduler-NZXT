import chromadb
import pandas as pd
import re
import json
from datetime import datetime
import os
import traceback
from config import ROLE_MAPPINGS

# Initialize ChromaDB client and collection
chroma_client = chromadb.PersistentClient(path="./chroma_db_nzxt")
employee_collection = chroma_client.get_or_create_collection(name="employees")

def normalize_role(role):
    """Normalize role names for consistent matching."""
    if not isinstance(role, str):
        role = str(role)
    role = role.lower().strip()
    role = re.sub(r'[^a-z0-9\s]', '', role)
    role = re.sub(r'\s+', '_', role)  # Use underscore for spaces
    role = re.sub(r's$', '', role)    # Remove trailing 's'
    return role

def read_employee_data(excel_file="C:/Users/rshah/Downloads/nzxt_employees.xlsx"):
    """
    Reads employee data from an Excel file and stores unique employees in ChromaDB.
    """
    try:
        # Try multiple potential file paths
        file_paths = [
            excel_file,
            os.path.join(os.path.dirname(__file__), excel_file),
            os.path.join(os.getcwd(), excel_file),
            "Employee Information Template.csv"
        ]
        
        # Find the first existing file
        actual_file = None
        for path in file_paths:
            if os.path.exists(path):
                actual_file = path
                break
        
        if not actual_file:
            print(f"ERROR: Could not find employee data file: {excel_file}")
            return 0
        
        print(f"Reading employee data from: {actual_file}")
        
        # Read the file based on its extension
        file_extension = os.path.splitext(actual_file)[1].lower()
        
        if file_extension == '.xlsx' or file_extension == '.xls':
            df = pd.read_excel(actual_file, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
        else:
            # Try different encodings for CSV
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(actual_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error reading with {encoding} encoding: {e}")
                    continue
            
            if df is None:
                raise Exception("Could not read file with any supported encoding")
        
        print("Columns in the file:", list(df.columns))
        
        # Define column mappings based on the actual Excel structure
        column_mapping = {
            'Company Code': 'Company Code',
            'Employee Id': 'Employee Id',
            'Last Name': 'Last Name',
            'Preferred First Name': 'First Name',
            'Hire Date': 'Hire Date',
            'Current Home Email': 'Email',
            'Supervisor': 'Supervisor',
            'Position Description': 'Job Title',
            'Account': 'Department Description'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert numeric columns to string
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        count = 0
        skipped = 0
        
        # Get existing employee IDs
        existing_employee_ids = set()
        try:
            existing_data = employee_collection.get()
            if existing_data and 'metadatas' in existing_data:
                for metadata in existing_data['metadatas']:
                    if 'employee_id' in metadata:
                        existing_employee_ids.add(metadata['employee_id'])
        except Exception as e:
            print(f"Warning: Could not retrieve existing employees: {e}")
        
        # Process each employee
        for _, row in df.iterrows():
            try:
                # Get employee ID
                employee_id = str(row['Employee Id']).strip()
                if employee_id.lower() == 'nan' or not employee_id:
                    print(f"Skipping employee with missing ID")
                    skipped += 1
                    continue
                
                # Check for duplicates
                if employee_id in existing_employee_ids:
                    print(f"Skipping duplicate employee ID: {employee_id}")
                    skipped += 1
                    continue
                
                # Get name information
                first_name = row['First Name'].strip()
                last_name = row['Last Name'].strip()
                full_name = f"{first_name} {last_name}".strip()
                
                if not full_name or first_name == 'nan' or last_name == 'nan':
                    print(f"Skipping employee with incomplete name: {employee_id}")
                    skipped += 1
                    continue

                # Process job title and skills
                job_title = str(row['Job Title']).strip()
                if job_title.lower() == 'nan':
                    job_title = "General Worker"
                
                # Normalize the job title for consistent matching
                normalized_job_title = normalize_role(job_title)
                
                # No skills or job title variations are added

                # Add department as a field if available
                department = str(row['Department Description']).strip()
                if department and department.lower() == 'nan':
                    department = ""

                # Get email and supervisor information
                email = str(row['Email']).strip() if 'Email' in row else ''
                supervisor = str(row['Supervisor']).strip() if 'Supervisor' in row else ''
                hire_date = str(row['Hire Date']).strip() if 'Hire Date' in row else ''
                
                # Create name variations
                name_variations = [
                    full_name,
                    f"{last_name}, {first_name}",
                    f"{first_name} {last_name}",
                    f"{first_name.lower()} {last_name.lower()}",
                    f"{last_name.lower()}, {first_name.lower()}"
                ]
                
                # Create employee metadata
                metadata = {
                    "name": full_name,
                    "name_variations": json.dumps(list(set(name_variations))),
                    "employee_id": employee_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "original_job_title": job_title,  # Keep original for reference
                    "normalized_job_title": normalized_job_title,  # Add normalized version
                    "department": department,
                    "email": email,
                    "supervisor": supervisor,
                    "hire_date": hire_date,
                    "last_updated": str(datetime.now().date()),
                }
                
                # Create employee document
                document = f"""Employee Name: {full_name}
                    Employee ID: {employee_id}
                    First Name: {first_name}
                    Last Name: {last_name}
                    Job Title: {job_title}
                    Department: {department}
                    Email: {email}
                    Supervisor: {supervisor}
                    Hire Date: {hire_date}
                    Last Updated: {metadata['last_updated']}"""

                # Add to ChromaDB
                employee_collection.upsert(ids=[employee_id], metadatas=[metadata], documents=[document])
                count += 1
                existing_employee_ids.add(employee_id)
                print(f"Added employee: {full_name}, ID: {employee_id}, Job: {job_title}")
            
            except Exception as e:
                print(f"Error processing employee row: {e}")
                traceback.print_exc()
                skipped += 1
                continue

        print(f"Successfully imported {count} employees")
        if skipped > 0:
            print(f"Skipped {skipped} invalid or duplicate entries")
        return count
    
    except Exception as e:
        print(f"Error reading employee data: {e}")
        traceback.print_exc()
        return 0

def retrieve_employees(required_roles):
    """
    Retrieves employees from ChromaDB matching the required roles.
    
    Args:
        required_roles: Dictionary of roles and their required counts
        
    Returns:
        Dictionary mapping roles to lists of available employee IDs
    """
    matched_employees = {}
    
    try:
        # Get all employees from the database
        all_employees = employee_collection.get()
        all_ids = all_employees.get("ids", [])
        all_metadatas = all_employees.get("metadatas", [])
        
        # Debug: Print all employees and their roles
        print("\nAvailable employees and their roles:")
        for i, metadata in enumerate(all_metadatas):
            print(f"ID: {all_ids[i]}, Job: {metadata.get('original_job_title', 'N/A')}, Skills: {metadata.get('skills', 'N/A')}")
        
        for role, count in required_roles.items():
            matched_employees[role] = []
            role_variations = ROLE_MAPPINGS.get(role, [role])
            role_variations = [normalize_role(r) for r in role_variations]
            
            print(f"\nLooking for role: {role}")
            print(f"Variations: {role_variations}")
            
            for i, metadata in enumerate(all_metadatas):
                # Get normalized job title and skills
                job_title = normalize_role(metadata.get("original_job_title", ""))
                skills = [normalize_role(s) for s in metadata.get("skills", "").split(',')]
                
                # Debug
                print(f"Checking employee {all_ids[i]}: Job={job_title}, Skills={skills}")
                
                # Check for matches in both job title and skills
                if any(variation in job_title or any(variation in skill for skill in skills) 
                      for variation in role_variations):
                    matched_employees[role].append(all_ids[i])
                    print(f"Matched employee {all_ids[i]} for role {role}")
            
            if not matched_employees[role]:
                print(f"Warning: No employees found for role {role}")
            elif len(matched_employees[role]) < count:
                print(f"Warning: Not enough employees for role {role}. Need {count}, found {len(matched_employees[role])}")
    
    except Exception as e:
        print(f"Error retrieving employees: {e}")
        traceback.print_exc()
    
    return matched_employees

if __name__ == "__main__":
    print("=== Employee Database Setup ===")
    
    try:
        employee_count = employee_collection.count()
        print(f"Current employee count: {employee_count}")
        
        if employee_count == 0:
            print("\nImporting employee data...")
            count = read_employee_data()
            print(f"Added {count} employees to the database")
        else:
            print("Employee data already exists in the database")
            
    except Exception as e:
        print(f"Error during database setup: {e}")
        traceback.print_exc()