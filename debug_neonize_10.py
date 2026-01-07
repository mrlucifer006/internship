import neonize.utils.jid
import neonize.proto.Neonize_pb2

print("neonize.utils.jid dir:", dir(neonize.utils.jid))
print("neonize.proto.Neonize_pb2 dir:", dir(neonize.proto.Neonize_pb2))

try:
    from neonize.proto.Neonize_pb2 import JID as ProtoJID
    print("Found JID in Neonize_pb2")
    jid = ProtoJID(user="919876543210", server="s.whatsapp.net")
    print(f"Created ProtoJID: {jid}")
except:
    print("Failed to create ProtoJID")
