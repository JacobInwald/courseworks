# Jacob Inwald 2150204 
import sys
from socket import socket, AF_INET, SOCK_DGRAM 
import time

if len(sys.argv) != 4: 
    print("Usage: python3 Receiver.py1 <Port> <Filename>")
    exit(1)

# Initialisation 
port = int(sys.argv[1])
filename = sys.argv[2]
N = int(sys.argv[3])
localhost = 'localhost'

print('Setting up socket ...')
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind((localhost, port)) # bind as a listener
print(f'Listening on port: {port} ...')

# Initialise required data storage 
recv_base = 0
buffer = [b'' for _ in range(N)]
done = False

with open(filename, 'wb') as f:
    while not done: # Listen loop
        pkt, addr = sock.recvfrom(1027) # receive data and account for header
        seq = int.from_bytes(pkt[0:2], byteorder='big') 
        
        if len(pkt) < 3:
            continue
        if seq < recv_base: 
            sock.sendto(seq.to_bytes(2, 'big'), addr) 
        elif recv_base <= seq < recv_base+N:
            sock.sendto(seq.to_bytes(2, 'big'), addr) # ack packet
            buffer[seq-recv_base] = pkt     # add packet to buffer

        while buffer[0] != b'': # append consecutive acked packets  
            pkt = buffer.pop(0) # get fst element in buffer
            f.write(pkt[3:]) # write
            done = bool(pkt[2]) or done
            recv_base += 1  # update window
            buffer.append(b'') # roll buffer
            print(f"received {recv_base} KB")


# Ensure sender exits
sock.settimeout(1)
n = 0
while n < 5:
    try: 
        pkt, addr = sock.recvfrom(1024+2+1)
        sock.sendto(bytes(pkt[0:2]), addr)
    except Exception:
        n += 1 

print('\nData written successfully!')

# wrap up work
sock.close()
