from neonize.utils import build_jid
import inspect

try:
    print(f"build_jid signature: {inspect.signature(build_jid)}")
    # Try using it
    jid = build_jid("919876543210@s.whatsapp.net")
    print(f"build_jid result: {jid}")
except Exception as e:
    print(f"build_jid usage failed: {e}")
