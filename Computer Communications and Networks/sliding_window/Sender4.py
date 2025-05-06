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
    Builds the packet with the ack and checksum
    """
    seq = seq.to_bytes(2, byteorder='big') # converts packet number to bytes
    eof = eof.to_bytes(1, byteorder='big') # converts eof to byte
    return seq + eof + data


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

# Load data
with open(filename, 'rb') as f:
    raw = f.read()
kb = len(raw) / 1024 # get size of file in KB

# initialise buffers
sndpkts = [make_pkt(seq, eof, data) for seq, (data, eof) in enumerate(chunks(raw, 1024))]
ackpkt = [False for _ in sndpkts]
timers = [-1.0 for _ in sndpkts]

lock = threading.Lock()

# Base variables 
nextseqnum = 0
base = 0


def time_out():
    """
    Implementation of timeout as given by textbook
    """
    global timers, lock
    while not ackpkt[-1]:
        with lock:
            for i, t in enumerate(timers[base:base+N]): # only loops through the window 
                if t < 0 or ackpkt[i+base]: # skip acked packets
                    continue
                if time.time()-t > retryTimeout: # resend non acked packets
                    sock.sendto(sndpkts[i+base], (remoteHost,port))
                    timers[i+base] = time.time() # reset timer
        time.sleep(retryTimeout/2) # prevents thread hogging 


def snd_pkt():
    """
    Implementation of sndpkt given by textbook
    """
    global nextseqnum, timers, lock
    while not ackpkt[-1]:
        with lock:
            if nextseqnum < min(base+N, len(sndpkts)): # send packets if any left or window isn't full
                sock.sendto(sndpkts[nextseqnum], (remoteHost, port))
                if timers[nextseqnum] < 0: # start timer on packet
                    timers[nextseqnum] = time.time()
                nextseqnum+=1


def rcv_ack(): 
    """
    Implementation of rcv_ack given by textbook
    """
    global base, ackpkt, recv_ack, lock, timers
    while not ackpkt[-1]:
        try:
            data, _ = sock.recvfrom(2) # attempt to get ack
        except Exception:
            return
        with lock:
            recv_ack = int.from_bytes(data, 'big') # parse ack
            ackpkt[recv_ack] = True # mark packet acked
            timers[recv_ack] = -1.0 # stop packet resend timer
            if not ackpkt[-1]: # update base to point to the most recent unacked packet
                base += next(i for i, _ in enumerate(ackpkt[base:]) if not _)


rcvack = threading.Thread(target=rcv_ack)
sndpkt = threading.Thread(target=snd_pkt)
timeout = threading.Thread(target=time_out)

# Start Execution
st = time.time()
timeout.start()
rcvack.start()
sndpkt.start()

rcvack.join()
sndpkt.join()
timeout.join()

print(f'{kb / (time.time() - st):3f}')

# wrap up 
sock.close()
