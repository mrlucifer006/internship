from neonize.client import NewClient
import inspect

try:
    print(f"is_on_whatsapp signature: {inspect.signature(NewClient.is_on_whatsapp)}")
except Exception as e:
    print(f"Could not get signature: {e}")
