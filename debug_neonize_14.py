from neonize.client import NewClient
import inspect

client = NewClient("temp.sqlite3")
methods = dir(client)
print("Looking for number data methods:")
print([m for m in methods if "what" in m.lower() or "on" in m.lower() or "check" in m.lower() or "query" in m.lower()])

# Specifically looking for IsOnWhatsApp or similar
try:
    print(f"IsOnWhatsApp: {client.IsOnWhatsApp}")
exceptAttributeError:
    print("IsOnWhatsApp not found")
