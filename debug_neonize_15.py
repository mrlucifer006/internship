from neonize.client import NewClient

client = NewClient("temp.sqlite3")
methods = dir(client)
print("Methods matching query:")
for m in methods:
    if "on" in m.lower() and "what" in m.lower():
        print(m)
    if "check" in m.lower():
        print(m)

# Try 'is_on_whatsapp'
if hasattr(client, 'is_on_whatsapp'):
     print("Found is_on_whatsapp")
if hasattr(client, 'IsOnWhatsApp'):
     print("Found IsOnWhatsApp")
