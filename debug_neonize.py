from neonize.client import NewClient
import inspect

print("Methods of NewClient:")
client = NewClient("temp_session.sqlite3")
for name in dir(client):
    if not name.startswith("_"):
        print(name)
