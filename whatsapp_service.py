import threading
import logging
import time
import os
import atexit
from neonize.client import NewClient
from neonize.events import ConnectedEv, DisconnectedEv
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message
from neonize.utils import build_jid
from neonize.exc import IsOnWhatsAppError
from cache_manager import add_to_whatsapp_queue, get_pending_whatsapp_messages, remove_from_whatsapp_queue, increment_whatsapp_attempts

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
        self.thread = None
        self._setup_events()
        
        # Register cleanup
        atexit.register(self.shutdown)
        
        # Start Queue Processor
        threading.Thread(target=self.process_queue, daemon=True, name="WhatsAppQueueProcessor").start()
        
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
            
        @self.client.event(DisconnectedEv)
        def on_disconnected(client, event):
            self.is_connected = False
            logger.warning("Bot Disconnected from WhatsApp!")

    def start(self):
        """Starts the client in a background thread with auto-reconnect."""
        if self.thread and self.thread.is_alive():
            logger.info("WhatsApp service thread already running.")
            return

        def run_client():
            while True:
                try:
                    logger.info("Starting WhatsApp client connection...")
                    # connect() blocks until disconnected
                    self.client.connect()
                    logger.warning("WhatsApp client connection closed (connect returned).")
                except Exception as e:
                    logger.error(f"WhatsApp client connection error: {e}")
                    # If an error occurred (like EOF), best to ensure we are disconnected
                    try:
                        self.client.disconnect()
                    except:
                        pass
                    
                    logger.info("Retrying in 5s...")
                    time.sleep(5) 
                
                self.is_connected = False
                time.sleep(2)

        # Name the thread for debugging
        self.thread = threading.Thread(target=run_client, name="WhatsAppBotThread", daemon=True)
        self.thread.start()

    def process_queue(self):
        """Background task to process pending messages."""
        logger.info("WhatsApp Queue Processor started.")
        while True:
            try:
                if self.is_connected:
                    pending = get_pending_whatsapp_messages()
                    for item in pending:
                        # Double check connection
                        if not self.is_connected:
                            break
                        
                        logger.info(f"Processing queued message ID {item['id']} for {item['phone']}")
                        
                        success = False
                        # We use the internal send logic directly but without the threaded wrapper
                        # to ensure synchronous processing in this queue thread
                        if item['message_type'] == 'text':
                            success = self._send_text_sync(item['phone'], item['message'])
                        elif item['message_type'] == 'image':
                            success = self._send_image_sync(item['phone'], item['image_path'], item['caption'])
                        
                        if success:
                            remove_from_whatsapp_queue(item['id'])
                            logger.info(f"Queue item {item['id']} sent successfully.")
                        else:
                            increment_whatsapp_attempts(item['id'])
                            logger.warning(f"Queue item {item['id']} failed. Attempts: {item['attempts'] + 1}")
                            # Backoff a bit if failing
                            time.sleep(2)
                            
                        time.sleep(1) # Pace out messages
                
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
            
            time.sleep(10) # Check queue every 10 seconds

    def _format_jid(self, phone):
        """Standardize phone number to JID format and return JID object."""
        # Remove non-digits
        clean = ''.join(filter(str.isdigit, phone))
        
        # If length is 10, prepend 91 (default India)
        if len(clean) == 10:
            clean = "+91" + clean
        
        # Use built-in helper to create JID with all required fields (RawAgent, etc)
        return build_jid(clean)

    def wait_for_connection(self, timeout=30):
        """Waits for the connection to be established."""
        if self.is_connected:
            return True
        
        logger.info("Waiting for WhatsApp connection...")
        start_time = time.time()
        while not self.is_connected:
            if time.time() - start_time > timeout:
                return False
            time.sleep(1)
        return True

    def _send_text_sync(self, phone, text):
        """Synchronous helper for queue processing"""
        try:
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) == 10:
                clean_phone = "91" + clean_phone
            
            jid = None
            try:
                result = self.client.is_on_whatsapp(clean_phone)
                if result:
                    item = result[0]
                    if hasattr(item, 'JID'): jid = item.JID
                    elif hasattr(item, 'jid'): jid = item.jid
            except:
                pass 

            if not jid:
                jid = build_jid(clean_phone)
            
            msg = Message(conversation=text)
            self.client.send_message(jid, msg)
            return True
        except Exception as e:
            logger.error(f"Sync send text failed: {e}")
            return False

    def _send_image_sync(self, phone, image_path, caption):
        """Synchronous helper for queue processing"""
        try:
             # Read file
            if not os.path.exists(image_path):
                return False
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) == 10:
                clean_phone = "91" + clean_phone
            
            jid = None
            try:
                result = self.client.is_on_whatsapp(clean_phone)
                if result:
                    item = result[0]
                    if hasattr(item, 'JID'): jid = item.JID
                    elif hasattr(item, 'jid'): jid = item.jid
            except:
                pass 

            if not jid:
                jid = build_jid(clean_phone)

            msg = self.client.build_image_message(img_bytes, caption=caption)
            self.client.send_message(jid, msg)
            return True
        except Exception as e:
            logger.error(f"Sync send image failed: {e}")
            return False

    def send_message(self, phone, text):
        """Send a text message asynchronously with retries."""
        logger.info(f"send_message called with phone={phone}")
        
        def run_send():
            max_retries = 3
            backoff_times = [2, 5, 10] 
            
            for attempt in range(max_retries):
                if not self.wait_for_connection(timeout=30): 
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection wait timed out. Retrying attempt {attempt+2}/{max_retries}...")
                        continue
                    else:
                        logger.error("Abort send. Adding to persistent queue.")
                        add_to_whatsapp_queue(phone, 'text', text=text)
                        return 

                # Clean phone number string 
                clean_phone = ''.join(filter(str.isdigit, phone))
                if len(clean_phone) == 10:
                    clean_phone = "91" + clean_phone
                
                try:
                    # Optimistic check
                    jid = None
                    try:
                        result = self.client.is_on_whatsapp(clean_phone)
                        if result:
                            item = result[0]
                            if hasattr(item, 'JID'): jid = item.JID
                            elif hasattr(item, 'jid'): jid = item.jid
                    except IsOnWhatsAppError as e:
                        logger.warning(f"is_on_whatsapp failed: {e}")
                        if "websocket not connected" in str(e) or "EOF" in str(e):
                             logger.warning("Detected disconnected websocket/EOF. Resetting connection state.")
                             self.is_connected = False
                             time.sleep(backoff_times[attempt])
                             continue 
                        pass 

                    if not jid:
                        logger.warning(f"No JID found for {clean_phone} (or check failed), using fallback")
                        jid = build_jid(clean_phone)

                    logger.info(f"Using JID: {jid}")
                    
                    msg = Message(conversation=text)
                    self.client.send_message(jid, msg)
                    
                    user_part = getattr(jid, 'user', getattr(jid, 'User', str(jid)))
                    logger.info(f"Message sent to {user_part} (Attempt {attempt+1})")
                    return # Success, exit loop
                    
                except Exception as e:
                    import traceback
                    logger.error(f"Failed to send WhatsApp message to {phone} (Attempt {attempt+1}): {e}")
                    
                    # Check for generic connection errors in message
                    err_str = str(e).lower()
                    if "websocket not connected" in err_str or "eof" in err_str or "closed" in err_str:
                        self.is_connected = False
                        
                    if attempt < max_retries - 1:
                         time.sleep(backoff_times[attempt])
                    elif attempt == max_retries - 1:
                         logger.error("Final failure. Queuing message.")
                         add_to_whatsapp_queue(phone, 'text', text=text)

        threading.Thread(target=run_send, daemon=True).start()
        return {"success": True, "message": "Message queued"}

    def send_image(self, phone, image_path, caption=""):
        """Send an image message asynchronously with retries."""
        
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return {"success": False, "message": "Image file not found"}

        # Read file synchronously
        try:
            with open(image_path, "rb") as f:
                _ = f.read()
        except Exception as e:
            logger.error(f"Failed to read image file {image_path}: {e}")
            return {"success": False, "message": f"Read failed: {e}"}

        def run_send(path_str):
            max_retries = 3
            backoff_times = [2, 5, 10]
            
            for attempt in range(max_retries):
                if not self.wait_for_connection(timeout=30):
                     if attempt < max_retries - 1:
                        logger.warning(f"Connection wait timed out. Retrying attempt {attempt+2}/{max_retries}...")
                        continue
                     else:
                        logger.error("Abort send. Adding to persistent queue.")
                        add_to_whatsapp_queue(phone, 'image', image_path=path_str, caption=caption)
                        return

                clean_phone = ''.join(filter(str.isdigit, phone))
                if len(clean_phone) == 10:
                    clean_phone = "91" + clean_phone
                
                try:
                    jid = None
                    try:
                        result = self.client.is_on_whatsapp(clean_phone)
                        if result:
                            # ... (same check as send_message)
                            item = result[0]
                            if hasattr(item, 'JID'): jid = item.JID
                            elif hasattr(item, 'jid'): jid = item.jid
                    except IsOnWhatsAppError as e:
                        logger.warning(f"is_on_whatsapp failed: {e}")
                        if "websocket not connected" in str(e) or "EOF" in str(e):
                             logger.warning("Detected disconnected websocket. Resetting connection state.")
                             self.is_connected = False
                             time.sleep(backoff_times[attempt])
                             continue
                        pass

                    if not jid:
                        jid = build_jid(clean_phone)

                    logger.info(f"Sending image to JID: {jid}")
                    
                    with open(path_str, "rb") as f:
                        img_bytes = f.read()

                    msg = self.client.build_image_message(
                        img_bytes,
                        caption=caption
                    )
                    self.client.send_message(jid, msg)
                    
                    user_part = getattr(jid, 'user', getattr(jid, 'User', str(jid)))
                    logger.info(f"Image sent to {user_part} (Attempt {attempt+1})")
                    return # Success
                    
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp image to {phone} (Attempt {attempt+1}): {e}")
                    
                    err_str = str(e).lower()
                    if "websocket not connected" in err_str or "eof" in err_str or "closed" in err_str:
                        self.is_connected = False
                        
                    if attempt < max_retries - 1:
                        time.sleep(backoff_times[attempt])
                    else:
                        logger.error("Final failure. Queuing message.")
                        add_to_whatsapp_queue(phone, 'image', image_path=path_str, caption=caption)

        # Pass bytes and path string (for extension) to thread
        threading.Thread(target=run_send, args=(image_path,), daemon=True).start()
        return {"success": True, "message": "Image queued"}

# Global instance
whatsapp_service = WhatsAppService()
