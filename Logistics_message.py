import pywhatkit 
import time 

def out_message(driver_name, driver_phone, vehicle_number, from_location, to_location):
    message = f"""
    New Logistics Entry!
    Driver name : {driver_name}
    Driver Phone : {driver_phone}
    Vehicle number : {vehicle_number}
    From location : {from_location}
    To location : {to_location}
    """
    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no="+919342672711",
            message=message,
            tab_close=True

        )
        time.sleep(5)
        return {
            "success" : True,
            "message" : "Message sent successfully"
        }
    except Exception as e:
        print(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success" : False,
            "message" : str(e)
        }

def in_message(driver_name, driver_phone, vehicle_number, po_number, from_location, to_location):
    message = f"""
    Logistics Exit!
    Driver name : {driver_name}
    Driver Phone : {driver_phone}
    Vehicle number : {vehicle_number}
    PO number : {po_number}
    From location : {from_location}
    To location : {to_location}
    """
    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no="+919342672711",
            message=message,
            tab_close=True

        )
        time.sleep(5)
        return {
            "success" : True,
            "message" : "Message sent successfully"
        }
    except Exception as e:
        print(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success" : False,
            "message" : str(e)
        }




