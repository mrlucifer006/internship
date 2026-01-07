import time
import logging
from whatsapp_service import whatsapp_service
from employee_db import get_employee_by_name
from visitor_service import get_visitor_by_id

logger = logging.getLogger(__name__)

def send_forwarding_notification(visitor_id, new_host, forwarder_name):
    """
    Check if new host is offline and send WhatsApp notification if so.
    """
    try:
        # 1. Check New Host Status
        host_data = get_employee_by_name({"name": new_host})
        
        # If host is found and is OFFLINE (status 0)
        if host_data and host_data != "Employee not found" and host_data.get('status') == 0:
                logger.info(f"Forwarded to Offline Host ({new_host}). Sending WhatsApp...")
                
                # 2. Get Visitor Details
                visitor = get_visitor_by_id(visitor_id)
                if visitor:
                    # Construct Message
                    msg_body = (
                        f"🚨 *New Visitor Forwarded*\n\n"
                        f"👤 *Visitor:* {visitor.get('name')}\n"
                        f"📞 *Phone:* {visitor.get('phone')}\n"
                        f"🏢 *Reason:* {visitor.get('reason')}\n"
                        f"📝 *Forwarded By:* {forwarder_name}\n\n"
                        f"Please log in to the portal to approve/deny."
                    )
                    
                    host_phone = host_data.get('phone')
                    if host_phone:
                        whatsapp_service.send_message(host_phone, msg_body)
                        logger.info("WhatsApp notification sent (Threaded via service).")
                    else:
                        logger.warning(f"Host {new_host} has no phone number.")
    except Exception as e:
        logger.error(f"Error sending forwarding notification: {e}")

def send_message(visitor_name,visitor_phone,reason,person_meet_name,person_meet_whatsapp):
    """Send visitor notification to host via WhatsApp."""
    message = (
        "Visitor Alert\n\n"
        f" {visitor_name} has come to meet you.\n"
        f" Reason for visit : {reason}\n"
    )

    try:
        # Use new service
        whatsapp_service.send_message(person_meet_whatsapp, message)
        
        logger.info(f"Visitor notification sent to {person_meet_name} at {person_meet_whatsapp}")
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


def host_message(visitor_name,visitor_phone,reason,person_meet_name,person_meet_whatsapp):
    """Send visit confirmation to visitor via WhatsApp."""
    message = (
        "Visit Alert\n\n"
        f" You are going to visit {person_meet_name}.\n"
        f" Reason for visit : {reason}\n"
    )

    try:
        # Use new service to send TO VISITOR
        whatsapp_service.send_message(visitor_phone, message)
        
        logger.info(f"Visit confirmation sent to visitor {visitor_name} at {visitor_phone}")
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
