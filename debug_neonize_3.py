try:
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message
    print("Successfully imported Message")
    msg = Message(conversation="Hello World")
    print("Created Message object")
    print(msg)
except Exception as e:
    print(f"Error: {e}")

from neonize.client import NewClient
client = NewClient("temp.sqlite3")
print([m for m in dir(client) if "build" in m])
