import time
import logging
from whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

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
