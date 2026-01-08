import threading
import logging
import time
import os
import atexit
from neonize.client import NewClient
from neonize.events import ConnectedEv
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message
from neonize.utils import build_jid

logger = logging.getLogger(__name__)

class WhatsAppService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WhatsAppService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Initialize client with session file
        self.session_file = "my_session.sqlite3"
        self.client = NewClient(self.session_file)
        self.is_connected = False
        self._setup_events()
        
        # Register cleanup
        atexit.register(self.shutdown)
        
        self._initialized = True
        logger.info("WhatsAppService initialized")

    def shutdown(self):
        """Gracefully disconnect the client."""
        try:
           if self.is_connected:
               logger.info("Shutting down WhatsApp Service...")
               # Suppress logging from neonize/underlying libs during disconnect
               logging.getLogger().setLevel(logging.ERROR)
               try:
                   self.client.disconnect()
               finally:
                   # Restore (though app is exiting, so not strictly crucial)
                   logging.getLogger().setLevel(logging.INFO)
                   
               self.is_connected = False
        except Exception as e:
            # We still want to see our own errors if any, but unlikely due to suppression above
            print(f"Error during WhatsApp shutdown: {e}")

    def _setup_events(self):
        @self.client.event(ConnectedEv)
        def on_connected(client, event):
            self.is_connected = True
            logger.info("✅ Bot Connected to WhatsApp!")

    def start(self):
        """Starts the client in a background thread."""
        def run_client():
            try:
                logger.info("Starting WhatsApp client connection...")
                # connect() blocks, so this thread stays alive
                self.client.connect()
            except Exception as e:
                logger.error(f"WhatsApp client failed: {e}")

        # Name the thread for debugging
        self.thread = threading.Thread(target=run_client, name="WhatsAppBotThread", daemon=True)
        self.thread.start()

    def _format_jid(self, phone):
        """Standardize phone number to JID format and return JID object."""
        # Remove non-digits
        clean = ''.join(filter(str.isdigit, phone))
        
        # If length is 10, prepend 91 (default India)
        if len(clean) == 10:
            clean = "+91" + clean
        
        # Use built-in helper to create JID with all required fields (RawAgent, etc)
        return build_jid(clean)

    def wait_for_connection(self, timeout=15):
        """Waits for the connection to be established."""
        if self.is_connected:
            return True
        
        logger.info("Waiting for WhatsApp connection...")
        start_time = time.time()
        while not self.is_connected:
            if time.time() - start_time > timeout:
                logger.warning(f"Connection wait timed out after {timeout}s")
                return False
            time.sleep(0.5)
        return True

    def send_message(self, phone, text):
        """Send a text message asynchronously."""
        logger.info(f"send_message called with phone={phone}")
        
        def run_send():
            if not self.wait_for_connection():
                logger.warning("WhatsApp not connected. Attempting to send anyway or queuing...")

            # Clean phone number string 
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) == 10:
                clean_phone = "91" + clean_phone
            
            try:
                logger.info(f"Calling is_on_whatsapp with {clean_phone}")
                result = self.client.is_on_whatsapp(clean_phone)
                
                jid = None
                if result:
                    item = result[0]
                    if hasattr(item, 'JID'): jid = item.JID
                    elif hasattr(item, 'jid'): jid = item.jid
                
                if not jid:
                    logger.warning(f"No JID found for {clean_phone}, using fallback")
                    jid = build_jid(clean_phone)

                logger.info(f"Using JID: {jid}")
                
                msg = Message(conversation=text)
                self.client.send_message(jid, msg)
                
                user_part = getattr(jid, 'user', getattr(jid, 'User', str(jid)))
                logger.info(f"Message sent to {user_part} (Async)")
            except Exception as e:
                import traceback
                logger.error(f"Failed to send WhatsApp message to {phone}: {e}\n{traceback.format_exc()}")

        threading.Thread(target=run_send, daemon=True).start()
        return {"success": True, "message": "Message queued"}

    def send_image(self, phone, image_path, caption=""):
        """Send an image message asynchronously."""
        
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return {"success": False, "message": "Image file not found"}

        # Read file synchronously to avoid race condition with temp file deletion
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            logger.error(f"Failed to read image file {image_path}: {e}")
            return {"success": False, "message": f"Read failed: {e}"}

        def run_send(img_bytes, path_str):
            if not self.wait_for_connection():
                logger.warning("WhatsApp not connected. sending might fail.")

            # Clean phone number string 
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) == 10:
                clean_phone = "91" + clean_phone
            
            try:
                result = self.client.is_on_whatsapp(clean_phone)
                
                jid = None
                if result:
                    item = result[0]
                    if hasattr(item, 'JID'): jid = item.JID
                    elif hasattr(item, 'jid'): jid = item.jid
                
                if not jid:
                    jid = build_jid(clean_phone)

                logger.info(f"Sending image to JID: {jid}")
                
                msg = self.client.build_image_message(
                    img_bytes,
                    caption=caption
                )
                self.client.send_message(jid, msg)
                
                user_part = getattr(jid, 'user', getattr(jid, 'User', str(jid)))
                logger.info(f"Image sent to {user_part} (Async)")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp image to {phone}: {e}")

        # Pass bytes and path string (for extension) to thread
        threading.Thread(target=run_send, args=(image_bytes, image_path), daemon=True).start()
        return {"success": True, "message": "Image queued"}

# Global instance
whatsapp_service = WhatsAppService()
