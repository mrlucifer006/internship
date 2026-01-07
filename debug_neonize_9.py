from neonize.utils.jid import JID

try:
    jid = JID.parse("919876543210@s.whatsapp.net")
    print(f"Parsed JID: {jid} Type: {type(jid)}")
except:
    print("JID.parse failed")

try:
    jid = JID("919876543210@s.whatsapp.net") # Constructor?
    print(f"Constructed JID: {jid}")
except:
    print("JID constructor failed")
