import pywhatkit 
import time 
import logging
import os
import pyautogui
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)

# Default logistics phone number
LOGISTICS_PHONE = os.getenv('LOGISTICS_PHONE_NUMBER', '+919342672711')


def compress_image(img_path, max_size_kb=100, quality_start=85):
    """
    Compress an image to the smallest possible size.
    Returns path to compressed image (temp file).
    """
    try:
        img = Image.open(img_path)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (max 800px on longest side)
        max_dimension = 800
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create temp file for compressed image
        temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(temp_fd)
        
        # Compress with decreasing quality until under max_size_kb
        quality = quality_start
        while quality > 10:
            img.save(temp_path, 'JPEG', quality=quality, optimize=True)
            file_size_kb = os.path.getsize(temp_path) / 1024
            
            if file_size_kb <= max_size_kb:
                break
            quality -= 10
        
        logger.info(f"Compressed image: {os.path.getsize(temp_path)/1024:.1f}KB (quality={quality})")
        return temp_path
        
    except Exception as e:
        logger.error(f"Image compression failed: {e}")
        return img_path  # Return original if compression fails


def out_message(driver_name, driver_phone, vehicle_number, from_location, to_location, vehicle_img_path=None):
    """Send logistics entry notification via WhatsApp with optional vehicle photo."""
    message = f"""New Logistics Entry!
Driver name : {driver_name}
Driver Phone : {driver_phone}
Vehicle number : {vehicle_number}
From location : {from_location}
To location : {to_location}"""
    
    if not LOGISTICS_PHONE:
        logger.warning("LOGISTICS_PHONE_NUMBER not configured. Skipping WhatsApp notification.")
        return {
            "success": False,
            "message": "Logistics phone number not configured"
        }
    
    compressed_path = None
    try:
        # If vehicle image is provided and exists, send image with caption
        if vehicle_img_path and os.path.exists(vehicle_img_path):
            logger.info(f"Compressing and sending WhatsApp image: {vehicle_img_path}")
            
            # Compress image before sending
            compressed_path = compress_image(vehicle_img_path)
            
            pywhatkit.sendwhats_image(
                receiver=LOGISTICS_PHONE,
                img_path=compressed_path,
                caption=message,
                wait_time=20,
                tab_close=True
            )
            # Wait for WhatsApp to load and press Enter to send
            time.sleep(3)
            pyautogui.press('enter')
        else:
            # Send text message only
            logger.info("No image provided, sending text only")
            pywhatkit.sendwhatmsg_instantly(
                phone_no=LOGISTICS_PHONE,
                message=message,
                wait_time=20,
                tab_close=True
            )
        
        time.sleep(3)
        logger.info(f"Logistics notification sent to {LOGISTICS_PHONE}")
        return {
            "success": True,
            "message": "Message sent successfully"
        }
    except Exception as e:
        logger.error(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success": False,
            "message": str(e)
        }
    finally:
        # Clean up temp file
        if compressed_path and compressed_path != vehicle_img_path and os.path.exists(compressed_path):
            try:
                os.remove(compressed_path)
            except:
                pass


def in_message(driver_name, driver_phone, vehicle_number, po_number, from_location, to_location, vehicle_img_path=None):
    """Send logistics exit notification via WhatsApp with optional vehicle photo."""
    message = f"""Logistics Exit!
Driver name : {driver_name}
Driver Phone : {driver_phone}
Vehicle number : {vehicle_number}
PO number : {po_number}
From location : {from_location}
To location : {to_location}"""
    
    if not LOGISTICS_PHONE:
        logger.warning("LOGISTICS_PHONE_NUMBER not configured. Skipping WhatsApp notification.")
        return {
            "success": False,
            "message": "Logistics phone number not configured"
        }
    
    compressed_path = None
    try:
        # If vehicle image is provided and exists, send image with caption
        if vehicle_img_path and os.path.exists(vehicle_img_path):
            logger.info(f"Compressing and sending WhatsApp image: {vehicle_img_path}")
            
            # Compress image before sending
            compressed_path = compress_image(vehicle_img_path)
            
            pywhatkit.sendwhats_image(
                receiver=LOGISTICS_PHONE,
                img_path=compressed_path,
                caption=message,
                wait_time=20,
                tab_close=True
            )
            # Wait for WhatsApp to load and press Enter to send
            time.sleep(3)
            pyautogui.press('enter')
        else:
            # Send text message only
            logger.info("No image provided, sending text only")
            pywhatkit.sendwhatmsg_instantly(
                phone_no=LOGISTICS_PHONE,
                message=message,
                wait_time=20,
                tab_close=True
            )
        
        time.sleep(3)
        logger.info(f"Logistics exit notification sent to {LOGISTICS_PHONE}")
        return {
            "success": True,
            "message": "Message sent successfully"
        }
    except Exception as e:
        logger.error(f"FAILED TO SEND WHATSAPP: {e}")
        return {
            "success": False,
            "message": str(e)
        }
    finally:
        # Clean up temp file
        if compressed_path and compressed_path != vehicle_img_path and os.path.exists(compressed_path):
            try:
                os.remove(compressed_path)
            except:
                pass


# Alias for backward compatibility
send_whatsapp_message = out_message
