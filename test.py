from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv
from neonize.utils import log
import os # Needed to read the file

# Initialize client
client = NewClient("my_session.sqlite3")

@client.event(ConnectedEv)
def on_connected(client, event):
    print("✅ Bot Connected to WhatsApp!")

@client.event(MessageEv)
def on_message(client, message):
    # Safely get text
    text = message.Message.conversation or message.Message.extendedTextMessage.text
    chat_id = message.Info.MessageSource.Chat
    
    # 1. Basic Text Reply
    if text and text.lower() == "ping":
        client.reply_message(chat_id, "Pong! 🤖", message)

    # 2. Send Image Logic
    elif text and text.lower() == "image":
        # Ensure you have a file named 'test.jpg' in the same folder
        if os.path.exists("test.jpg"):
            
            # Step A: Read the file as bytes
            with open("test.jpg", "rb") as f:
                image_bytes = f.read()
            
            # Step B: Build the image message object
            # This uploads the image to WhatsApp servers and prepares the packet
            image_msg = client.build_image_message(
                image_bytes, 
                caption="Here is the image you asked for! 📸",
                mime_type="image/jpeg" # Change to image/png if using a PNG
            )
            
            # Step C: Send the message object
            client.send_message(chat_id, image_msg)
            print("Image sent successfully!")
        else:
            client.reply_message(chat_id, "❌ Error: 'test.jpg' not found in folder.", message)

client.connect()