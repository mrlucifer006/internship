from neonize.utils.jid import JID
import inspect

# Try to find a function that returns a JID
import neonize.utils
print("neonize.utils attributes:", [x for x in dir(neonize.utils) if "JID" in x or "jid" in x])

import neonize.utils.jid
print("neonize.utils.jid attributes:", [x for x in dir(neonize.utils.jid)])

# Try constructing with 0s
try:
    jid = JID(User="919876543210", Server="s.whatsapp.net", RawAgent=0, Device=0, Integrator=0)
    print(f"Constructed full JID: {jid}")
except Exception as e:
    print(f"Failed full JID: {e}")
