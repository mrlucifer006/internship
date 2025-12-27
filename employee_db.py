# employee_db.py

# specific dummy data for demonstration
# In a real app, this would query a database
EMPLOYEES = {
    "Sanjai": "+919342672711",
    "Naveen": "+919952747859",
    "Test Host": "+919998887776"
}

def get_employee_phone(name):
    """
    Returns the phone number for the given employee name.
    Returns None if not found.
    Case-insensitive lookup.
    """
    if not name:
        return None
        
    normalized_name = name.strip().lower()
    
    for emp_name, phone in EMPLOYEES.items():
        if emp_name.lower() == normalized_name:
            return phone
            
    return None

def init_employee_db():
    # Placeholder for DB initialization if needed later
    pass
