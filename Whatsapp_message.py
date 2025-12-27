import pywhatkit
import time

def send_message(visitor_name,visitor_phone,reason,person_meet_name,person_meet_whatsapp):
    message = (
        "Visitor Alert\n\n"
        f" {visitor_name} has come to meet you.\n"
        f" Reason for visit : {reason}\n"
    )

    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no = person_meet_whatsapp,
            message = message,
            tab_close = True
        )

        time.sleep(5)

        return {
            "success" : True,
            "message" : "Message sent successfully"
        }
    
    except Exception as e:
        # Prevent server crash if browser fails
        print(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success" : False,
            "message" : str(e)
        }


def host_message(visitor_name,visitor_phone,reason,person_meet_name,person_meet_whatsapp):
    message = (
        "Visit Alert\n\n"
        f" You are going to visit {person_meet_name}.\n"
        f" Reason for visit : {reason}\n"
    )

    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no = visitor_phone,
            message = message,
            tab_close = True
        )

        time.sleep(5)

        return {
            "success" : True,
            "message" : "Message sent successfully"
        }
    
    except Exception as e:
        # Prevent server crash if browser fails
        print(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success" : False,
            "message" : str(e)
        }



