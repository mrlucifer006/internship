from neonize.client import NewClient
import inspect
import sys

# Redirect stdout to ensure we catch everything
sys.stdout.reconfigure(encoding='utf-8')

client = NewClient("my_session.sqlite3")

print("\n--- SIGNATURE ---")
try:
    sig = inspect.signature(client.build_image_message)
    print(str(sig)) # Print string representation
except Exception as e:
    print(f"Error: {e}")

print("\n--- DOCSTRING ---")
print(client.build_image_message.__doc__)

print("\n--- ANNOTATIONS ---")
print(client.build_image_message.__annotations__)
