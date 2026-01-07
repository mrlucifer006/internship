from neonize.client import NewClient
import inspect

client = NewClient("temp.sqlite3")
# The signature in previous debug output was `(to: 'JID', ...)`
# We need to find where JID class is.

# Try to find JID in neonize.utils or just print client's module structure
import neonize
print(dir(neonize))

try:
    from neonize.utils import JID
    print("Found JID in utils")
except:
    pass
