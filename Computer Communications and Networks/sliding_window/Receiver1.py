# Jacob Inwald 2150204 

import sys
from socket import socket, AF_INET, SOCK_DGRAM 

if len(sys.argv) != 3: 
    print("Usage: python3 Receiver.py1 <Port> <Filename>")
    exit(1)

# Initialisation 
port = int(sys.argv[1])
filename = sys.argv[2]
localhost = 'localhost'

print('Setting up socket ...')
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind((localhost, port)) # bind as a listener

print(f'Listening on port: {port} ...')

# Initialise required data storage 
seq_nums = []
eof = False
with open(filename, 'wb') as f:
    while not eof: # Listen loop
        pkt, addr = sock.recvfrom(1027) # receive data
        seq = int.from_bytes(pkt[:2], byteorder='big') 
        eof = bool(pkt[2])

        if seq in seq_nums: # skips seen packets
            print(f"pkt {seq}: skipped")
            continue
        seq_nums.append(seq) # adds seq number to seen packets
        
        print(f"pkt {seq}: received {len(pkt)} bytes")
    
        f.write(pkt[3:])

# wrap up work
sock.close()
