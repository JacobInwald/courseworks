# Jacob Inwald 2150204

import sys
from socket import socket, AF_INET, SOCK_DGRAM 
import time


if len(sys.argv) != 4:
    print('Usage: python3 Sender1.py <RemoteHost> <Port> <Filename>')
    exit(1)

# Initialisation
remoteHost = sys.argv[1]
port = int(sys.argv[2])
filename = sys.argv[3]

# Open socket
print('Setting up socket ...')
sock = socket(AF_INET, SOCK_DGRAM)

# Load data
print('Reading file ...')
i = 0
with open(filename, 'rb') as f:
    while len(f.peek()) > 0:
        seq = i.to_bytes(2, 'big') # converts packet number to bytes
        chunk = f.read(1024) # read chunk of data
        eof = (len(f.peek()) == 0).to_bytes(1, 'big') # converts eof to byte
        pkt = seq + eof + chunk # construct packet

        sock.sendto(pkt, (remoteHost, port)) # sent to specified host and port
        print(f'\rpkt {i}: sent {len(pkt)} bytes', end='')
        
        time.sleep(0.01) # account for delay of packets
        i += 1

# wrap up 
sock.close()
print('\nDone!')

