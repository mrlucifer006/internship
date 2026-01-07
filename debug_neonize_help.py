from neonize.client import NewClient
import inspect

client = NewClient("temp.sqlite3")
print("Help for send_message:")
help(client.send_message)
