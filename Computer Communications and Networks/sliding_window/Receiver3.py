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
expseqnum = 0
ackpkt = expseqnum.to_bytes(2, 'big')

with open(filename, 'wb') as f:
    while True: # Listen loop
        pkt, addr = sock.recvfrom(1024+2+1) # receive data and account for header
        seq = int.from_bytes(pkt[0:2], byteorder='big')  
        eof = pkt[2]

        if len(pkt) <= 2 or seq != expseqnum: # case of wrong packet
            sock.sendto(ackpkt, addr) # ack most recent
            continue

        f.write(pkt[3:]) # append bytes to raw data
        ackpkt = expseqnum.to_bytes(2, 'big')
        sock.sendto(ackpkt, addr) # ack
        expseqnum += 1 
        
        print(f"received {expseqnum} KB")
        if eof == 1:
            break

    # Ensure sender quits
    expseqnum += 1
    for i in range(50):
        sock.sendto(expseqnum.to_bytes(2, 'big'), addr)
        time.sleep(0.01)

print('Done!')

# wrap up work
sock.close()
