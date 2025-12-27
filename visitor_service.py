from app.db import mongo
from datetime import datetime

def save_visitor(data):
    """
    Validates and saves visitor data.
    Expected keys: name, phone, person_to_visit, reason, has_vehicle, vehicle_number (optional)
    """
    errors = []
    
    # Basic Validation
    if not data.get("name"):
        errors.append("Name is required.")
    if not data.get("phone"):
        errors.append("Phone number is required.")
    if not data.get("person_to_visit"):
        errors.append("Person to visit is required.")
    if not data.get("reason"):
        errors.append("Reason for visit is required.")
    
    has_vehicle = data.get("has_vehicle")
    vehicle_number = data.get("vehicle_number")
    
    # Normalize boolean check (handle string "true"/"false" if coming from form)
    if isinstance(has_vehicle, str):
        has_vehicle = has_vehicle.lower() == 'true'
    
    if has_vehicle and not vehicle_number:
        errors.append("Vehicle registration number is required if vehicle is present.")

    # Duplicate Check
    active_visitor = mongo.db.visitors.find_one({
        "name": data["name"],
        "phone": data["phone"],
        "exit_time": None
    })

    if active_visitor:
        return {"success": False, "errors": ["Visitor already checked in and has not exited."]}

    if errors:
        return {"success": False, "errors": errors}

    # Construct Document
    visitor_doc = {
        "name": data["name"],
        "phone": data["phone"],
        "person_to_visit": data["person_to_visit"],
        "reason": data["reason"],
        "has_vehicle": bool(has_vehicle),
        "vehicle_number": vehicle_number if has_vehicle else None,
        "entry_time": datetime.utcnow(),
        "exit_time": None
    }

    try:
        mongo.db.visitors.insert_one(visitor_doc)
        return {"success": True, "message": "Visitor registered successfully."}
    except Exception as e:
        return {"success": False, "errors": [str(e)]}

def check_out_visitor(data):
    """
    Marks a visitor as exited.
    Expected keys: name, phone
    """
    if not data.get("name") or not data.get("phone"):
        return {"success": False, "errors": ["Name and Phone number are required."]}

    result = mongo.db.visitors.update_one(
        {
            "name": data["name"],
            "phone": data["phone"],
            "exit_time": None
        },
        {"$set": {"exit_time": datetime.utcnow()}}
    )

    if result.modified_count > 0:
        return {"success": True, "message": "Visitor checked out successfully."}
    else:
        return {"success": False, "errors": ["No active check-in found for this visitor."]}
