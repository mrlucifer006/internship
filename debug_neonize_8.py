import neonize
import inspect
import pkgutil

def find_jid(module):
    if hasattr(module, 'JID'):
        print(f"Found JID in {module.__name__}")
    
    if hasattr(module, '__path__'):
        for _, name, ispkg in pkgutil.iter_modules(module.__path__):
            try:
                submod = __import__(f"{module.__name__}.{name}", fromlist=[''])
                if hasattr(submod, 'JID'):
                     print(f"Found JID in {submod.__name__}")
                if ispkg:
                    find_jid(submod)
            except:
                pass

find_jid(neonize)

from neonize.client import NewClient
print(f"Client send_message annotations: {NewClient.send_message.__annotations__}")
