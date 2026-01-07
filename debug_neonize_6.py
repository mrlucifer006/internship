import neonize.utils
import neonize.types
import neonize.proto

print("neonize.utils dir:", dir(neonize.utils))
print("neonize.types dir:", dir(neonize.types))

try:
    from neonize.utils import JID
    print("Found JID in neonize.utils")
except:
    print("Not in utils")

try:
    from neonize.types import JID
    print("Found JID in neonize.types")
except:
    print("Not in types")
