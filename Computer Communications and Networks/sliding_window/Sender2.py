# Jacob Inwald s2150204

import sys
from socket import socket, AF_INET, SOCK_DGRAM, timeout
import time



def make_pkt(ack, eof, data):
    """
    Builds the packet with the ack and checksum
    """
    ack = ack.to_bytes(2, byteorder='big') # converts packet number to bytes
    eof = eof.to_bytes(1, byteorder='big') # converts eof to byte
    return ack + eof + data   # construct packet


if len(sys.argv) != 5:
    print('Usage: python3 Sender2.py <RemoteHost> <Port> <Filename> <RetryTimeout>')
    exit(1)

# Initialisation
remoteHost = sys.argv[1]
port = int(sys.argv[2])
filename = sys.argv[3]
retryTimeout = int(sys.argv[4])

# Load data
with open(filename, 'rb') as f:
    raw = f.read()

kb = len(raw) / 1024
# Open socket
sock = socket(AF_INET, SOCK_DGRAM)
sock.settimeout(retryTimeout/1000)



def send_pkt(pkt):
    """
    Sends the packet with the given data 
    """
    retrans = 0
    sock.sendto(pkt, (remoteHost, port)) # start send
    
    while True: 
        try: # Try and get ack
            data, _ = sock.recvfrom(2)
            recv_ack = int.from_bytes(data, 'big')
        except timeout:
            recv_ack = None
        
        if ack == recv_ack: # if correctly acked stop
            break
        # retransmit
        sock.sendto(pkt, (remoteHost, port))
        retrans+=1
    
    return retrans


# Send data
ack = 1
retransmissions = 0
st = time.time()
with open(filename, 'rb') as f:
    while len(f.peek()) > 0:
        ack ^= 1 # flip ack
        data = f.read(1024) # get next chunk
        pkt = make_pkt(ack, len(f.peek()) == 0, data)
        retransmissions += send_pkt(pkt) # send pkt

print(f'{retransmissions}    {kb / (time.time() - st):.2f}')

# wrap up 
sock.close()
