from neonize.client import NewClient
import inspect

# Use existing session file to avoid re-login or just dry run
client = NewClient("my_session.sqlite3")

try:
    sig = inspect.signature(client.build_image_message)
    print(f"Signature of build_image_message: {sig}")
except Exception as e:
    print(f"Error inspecting signature: {e}")
    # Try dir
    print(dir(client))
