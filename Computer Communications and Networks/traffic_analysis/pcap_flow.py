from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP
from scapy.layers.inet6 import IPv6
from ipaddress import ip_address, IPv6Address
from socket import IPPROTO_TCP
import sys
import matplotlib.pyplot as plt


class Flow(object):
    def __init__(self, data):
        self.pkts = 0
        self.flows = 0
        self.ft = {}
        for pkt, metadata in RawPcapReader(data):
            self.pkts += 1
            ether = Ether(pkt)
            # INSERT CODE
            if ether.type == 0x86dd:
                ip = ether[IPv6]
                ip_src = int(IPv6Address(ip.src))# Convert the IPv6 address to an object
                ip_dst = int(IPv6Address(ip.dst)) # Convert the IPv6 address to an object
                if ip.nh != IPPROTO_TCP: # Check if the next header is TCP
                    continue
                size = ip.plen
            elif ether.type == 0x0800:
                ip = ether[IP]
                ip_src = int(ip_address(ip.src)) # Convert the IPv4 address to an object
                ip_dst = int(ip_address(ip.dst)) # Convert the IPv4 address to an object
                if ip.proto != IPPROTO_TCP: # Check if the next header is TCP
                    continue
                size = ip.len - (4*ip.ihl) 
            else:
                continue
            
            if TCP in ip: # Check if the packet has a TCP layer
                tcp = ip[TCP]
            else:
                continue

            k = (ip_src, ip_dst, tcp.sport, tcp.dport) # Create a key for the flow
            rk = (k[1], k[0], k[3], k[2])
            size = size - 4*tcp.dataofs
            if rk in self.ft.keys(): # Check if the alternative key is in the flow table
                self.ft[rk] += size
            elif k in self.ft.keys(): # If key in flow table append otherwise 
                self.ft[k] += size 
            else: # If key not in flow table add it
                self.flows += 1
                self.ft[k] = size
            # INSERT CODE
    def Plot(self):
        topn = 100
        data = [i/1000 for i in list(self.ft.values())]
        data.sort()
        data = data[-topn:]
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.hist(data, bins=50, log=True)
        ax.set_ylabel('# of flows')
        ax.set_xlabel('Data sent [KB]')
        ax.set_title('Top {} TCP flow size distribution.'.format(topn))
        plt.savefig(sys.argv[1] + '.flow.pdf', bbox_inches='tight')
        plt.close()
    def _Dump(self):
        with open(sys.argv[1] + '.flow.data', 'w') as f:
            f.write('{}'.format(self.ft))

if __name__ == '__main__':
    d = Flow(sys.argv[1])
    d.Plot()
    d._Dump()
