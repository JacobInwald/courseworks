# Jacob Inwald 2150204 
import sys
from socket import socket, AF_INET, SOCK_DGRAM 
import time 

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
expack = 0
i = 0
eof = 0
addr = ('' , '')
with open(filename, 'wb') as f: 
    while eof != 1: # Listen loop
        pkt, addr = sock.recvfrom(1027) # receive data and account for header
        ack = int.from_bytes(pkt[:2], 'big')
        eof = pkt[2]

        if ack != expack or len(pkt) < 3:
            sock.sendto((expack^1).to_bytes(2, 'big'), addr)
            continue

        sock.sendto(expack.to_bytes(2, 'big'), addr)
        expack ^= 1 # flip expected ack
     
        print(f"pkt {ack}: received {i} KB")
        i += 1 
        f.write(pkt[3:]) # append bytes to raw data

# ensure completion
for i in range(50):
    expack ^= 1
    sock.sendto(expack.to_bytes(2, 'big'), addr)
    time.sleep(0.01)

print('\nDone!')
# wrap up work
sock.close()
