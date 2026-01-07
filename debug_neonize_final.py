from neonize.client import NewClient
from neonize.types import JID
import inspect

print("Checking JID type...")
try:
    my_jid = JID(User="919876543210", Server="s.whatsapp.net")
    print(f"Created JID object: {my_jid}")
except Exception as e:
    print(f"Error creating JID: {e}")

try:
    parsed_jid = JID.parse("919876543210@s.whatsapp.net")
    print(f"Parsed JID: {parsed_jid}")
except Exception as e:
    print(f"Error parsing JID: {e}")

client = NewClient("temp.sqlite3")
try:
    sig = inspect.signature(client.send_message)
    print(f"client.send_message signature: {sig}")
except:
    print("Could not get signature")
