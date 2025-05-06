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
            if ether.type == 0x86dd:
                ip = ether[IPv6]
                if ip.nh != IPPROTO_TCP:
                    continue
                plen = ip.plen
                sip = int(IPv6Address(ip.src))
                dip = int(IPv6Address(ip.dst))
            elif ether.type == 0x0800:
                ip = ether[IP]
                if ip.proto != IPPROTO_TCP:
                    continue
                plen = ip.len - ip.ihl * 4
                sip = int(ip_address(ip.src))
                dip = int(ip_address(ip.dst))
            if not ip.haslayer(TCP):
                continue
            tcp = ip[TCP]
            plen -= tcp.dataofs * 4
            if plen == 0:
                continue
            tcpflow = (sip, dip, tcp.sport, tcp.dport)
            rflow = (dip, sip, tcp.dport, tcp.sport)
            if tcpflow in self.ft:
                self.ft[tcpflow] += plen
            elif rflow in self.ft:
                self.ft[rflow] += plen
            else:
                self.ft[tcpflow] = plen
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
