from neonize.utils.jid import JID
import inspect

print(f"JID type: {type(JID)}")
try:
    print(f"JID doc: {JID.__doc__}")
except:
    pass

try:
    print(f"JID signature: {inspect.signature(JID)}")
except:
    pass
    
try:
    # Try creating with user/server
    jid = JID(User="919876543210", Server="s.whatsapp.net")
    print(f"Created JID(User=...): {jid}")
except Exception as e:
    print(f"Failed JID(User=...): {e}")

try:
    # Try Jid2String
    from neonize.utils.jid import Jid2String
    print("Jid2String found")
except:
    print("Jid2String not found")
