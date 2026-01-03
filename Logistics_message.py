import pywhatkit 
import time 
import logging
import os

logger = logging.getLogger(__name__)

def out_message(driver_name, driver_phone, vehicle_number, from_location, to_location):
    """Send logistics entry notification via WhatsApp."""
    message = f"""
    New Logistics Entry!
    Driver name : {driver_name}
    Driver Phone : {driver_phone}
    Vehicle number : {vehicle_number}
    From location : {from_location}
    To location : {to_location}
    """
    
    # Get phone number from environment variable
    logistics_phone = os.getenv('LOGISTICS_PHONE_NUMBER', '')
    
    if not logistics_phone:
        logger.warning("LOGISTICS_PHONE_NUMBER not configured. Skipping WhatsApp notification.")
        return {
            "success": False,
            "message": "Logistics phone number not configured"
        }
    
    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no=logistics_phone,
            message=message,
            tab_close=True

        )
        time.sleep(5)
        logger.info(f"Logistics notification sent to {logistics_phone}")
        return {
            "success" : True,
            "message" : "Message sent successfully"
        }
    except Exception as e:
        logger.error(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success" : False,
            "message" : str(e)
        }

def in_message(driver_name, driver_phone, vehicle_number, po_number, from_location, to_location):
    """Send logistics exit notification via WhatsApp."""
    message = f"""
    Logistics Exit!
    Driver name : {driver_name}
    Driver Phone : {driver_phone}
    Vehicle number : {vehicle_number}
    PO number : {po_number}
    From location : {from_location}
    To location : {to_location}
    """
    
    # Get phone number from environment variable
    logistics_phone = os.getenv('LOGISTICS_PHONE_NUMBER', '')
    
    if not logistics_phone:
        logger.warning("LOGISTICS_PHONE_NUMBER not configured. Skipping WhatsApp notification.")
        return {
            "success": False,
            "message": "Logistics phone number not configured"
        }
    
    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no=logistics_phone,
            message=message,
            tab_close=True

        )
        time.sleep(5)
        logger.info(f"Logistics exit notification sent to {logistics_phone}")
        return {
            "success" : True,
            "message" : "Message sent successfully"
        }
    except Exception as e:
        logger.error(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success" : False,
            "message" : str(e)
        }


# Alias for backward compatibility
send_whatsapp_message = out_message
