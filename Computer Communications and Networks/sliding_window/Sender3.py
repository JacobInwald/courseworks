# Jacob Inwald 2150204
import sys
from socket import socket, AF_INET, SOCK_DGRAM 
import time
import threading 


def chunks(lst, n):
    """
        Yield successive n-sized chunks from lst.
        The last chunk is flagged with True to signify end of packet stream
    """
    l_n = (len(lst) // n)
    l_n -= int(l_n*n==len(lst)) # case where the list is divisible by end
    for i in range(l_n):
        yield lst[i*n:i*n + n], False

    yield lst[l_n*n:], True


def make_pkt(seq, eof, data):
    """
    Builds the packet with the seq
    """
    seq = seq.to_bytes(2, byteorder='big') # converts packet number to bytes
    eof = eof.to_bytes(1, byteorder='big') # converts eof to byte
    return seq + eof + data  # construct packet



if len(sys.argv) != 6:
    print('Usage: python3 Sender3.py <RemoteHost> <Port> <Filename> <RetryTimeout> <WindowSize>')
    exit(1)


# Initialisation
remoteHost = sys.argv[1]
port = int(sys.argv[2])
filename = sys.argv[3]
retryTimeout = int(sys.argv[4]) / 1000
N = int(sys.argv[5])

# Open socket
sock = socket(AF_INET, SOCK_DGRAM)

# Base variables
nextseqnum = 0
base = 0
timer = -1

# Load data
with open(filename, 'rb') as f:
    raw = f.read()
kb = len(raw) / 1024 # get size of data in KB
sndpkt = [make_pkt(seq, eof, data) for seq, (data, eof) in enumerate(chunks(raw, 1024))]
lock = threading.Lock()


def time_out():
    """
    Implementation of timeout as given by textbook
    """
    global timer, lock
    while base < len(sndpkt):
        with lock:
            if time.time() - timer > retryTimeout and timer != -1:
                timer = time.time() # reset timer
                [sock.sendto(sndpkt[i], (remoteHost, port)) for i in range(base, nextseqnum, 1)] # send all packets
        time.sleep(retryTimeout / 2) # prevents flooding            


def send_pkt():
    """
    Implementation of send_pkt as given by textbook
    """
    global nextseqnum, timer, lock
    while base < len(sndpkt):
        with lock:    
            if nextseqnum < min(base+N, len(sndpkt)): # runs if there is a next packet and window has space
                sock.sendto(sndpkt[nextseqnum], (remoteHost, port))
                if base == nextseqnum and timer == -1: # start timer for packet
                    timer = time.time() 
                nextseqnum+=1 # update nextseqnum


def rcv_ack():
    """
    Implementation of rcv_ack as given by textbook
    """
    global base, timer, lock
    while base < len(sndpkt):
        try:
            data, _ = sock.recvfrom(2) # attempt to get ack
        except Exception:
            continue 
        with lock:
            recv_ack = int.from_bytes(data[:2], 'big')
            base=recv_ack+1 # update base with recv_ack
            if base==nextseqnum: # stop timer if window is empty
                timer = -1 
            elif timer == -1: # otherwise start timer
                timer = time.time()


# Start Execution
sendpkt = threading.Thread(target=send_pkt)
rcvack = threading.Thread(target=rcv_ack)
timeout = threading.Thread(target=time_out)

st = time.time()
timeout.start()
rcvack.start()
sendpkt.start()

# wait for completion
rcvack.join()
sendpkt.join()
timeout.join()

print(f'{kb / (time.time() - st):.2f}')

# wrap up 
sock.close()
