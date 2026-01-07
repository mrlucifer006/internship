from neonize.client import NewClient
import inspect

client = NewClient("temp_session.sqlite3")

print("\n--- Methods ---")
methods = [m for m in dir(client) if not m.startswith("_")]
for m in sorted(methods):
    print(m)

print("\n--- send_message Signature ---")
try:
    print(inspect.signature(client.send_message))
except Exception as e:
    print(f"Error: {e}")
