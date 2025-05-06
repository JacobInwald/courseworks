from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP
from ipaddress import ip_address, ip_network
import sys
import matplotlib.pyplot as plt

class Node(object):
    def __init__(self, ip, plen):
        self.bytes = plen
        self.left = None
        self.right = None
        self.ip = ip
 
    def add(self, ip, plen):
        # INSERT CODE
        if ip < self.ip:
            if self.left is None:
                self.left = Node(ip, plen)
            else:
                self.left.add(ip, plen)
        elif ip > self.ip:
            if self.right is None:
                self.right = Node(ip, plen)
            else: 
                self.right.add(ip, plen)
        elif ip == self.ip:
            self.bytes += plen
        # END INSERT CODE

    def data(self, data):
        if self.left:
            self.left.data(data)
        if self.bytes > 0:
            data[ip_network(self.ip)] = self.bytes
        if self.right:
            self.right.data(data)

    @staticmethod 
    def supernet(ip1, ip2):
        na1 = ip_network(ip1).network_address
        na2 = ip_network(ip2).network_address
        # INSERT CODE 
        supernet = ip_network(na1)
        while not supernet.supernet_of(ip_network(na2)):
            supernet = supernet.supernet(1)
        
        return ip_network('{}/{}'.format(supernet.network_address, supernet.netmask), strict=False)
        # END INSERT CODE
        
    def aggr(self, byte_thresh):
        # INSERT CODE
        if not self.left and not self.right: # ignore leaf node
            return

        # Aggregate the left and right subtrees first
        if self.left:
            self.left.aggr(byte_thresh)
        if self.right:
            self.right.aggr(byte_thresh)

        # Aggregate the current node, if necessary
        if self.left and self.left.bytes < byte_thresh:
            self.ip = self.supernet(self.left.ip, self.ip)
            self.bytes = self.left.bytes + self.bytes
            self.left.bytes = 0
            if not self.left.right and not self.left.left:
                self.left = None
        
        # Aggregate the current node, if necessary
        if self.right and self.right.bytes < byte_thresh:
            self.ip = self.supernet(self.right.ip, self.ip)
            self.bytes = self.right.bytes + self.bytes
            self.right.bytes = 0 
            if not self.right.right and not self.right.left:
                self.right = None
        # END INSERT CODE
            
class Data(object):
    def __init__(self, data):
        self.tot_bytes = 0
        self.data = {}
        self.aggr_ratio = 0.05
        root = None
        cnt = 0
        for pkt, metadata in RawPcapReader(data):
            ether = Ether(pkt)
            if not 'type' in ether.fields:
                continue
            if ether.type != 0x0800:
                continue
            ip = ether[IP]
            self.tot_bytes += ip.len
            if root is None:
                root = Node(ip_address(ip.src), ip.len)
            else:
                root.add(ip_address(ip.src), ip.len)
            cnt += 1
        root.aggr(self.tot_bytes * self.aggr_ratio)
        root.data(self.data)
    def Plot(self):
        data = {k: v/1000 for k, v in self.data.items()}
        plt.rcParams['font.size'] = 8
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(which='major', axis='y')
        ax.tick_params(axis='both', which='major')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels([str(l) for l in data.keys()], rotation=45,
            rotation_mode='default', horizontalalignment='right')
        ax.set_ylabel('Total bytes [KB]')
        ax.bar(ax.get_xticks(), data.values(), zorder=2)
        ax.set_title('IPv4 sources sending {} % ({}KB) or more traffic.'.format(
            self.aggr_ratio * 100, self.tot_bytes * self.aggr_ratio / 1000))
        plt.savefig(sys.argv[1] + '.aggr.pdf', bbox_inches='tight')
        plt.close()
    def _Dump(self):
        with open(sys.argv[1] + '.aggr.data', 'w') as f:
            f.write('{}'.format({str(k): v for k, v in self.data.items()}))

if __name__ == '__main__':
    d = Data(sys.argv[1])
    d.Plot()
    d._Dump()


# Helpers

def print_tree(node):
    if node.left:
        print_tree(node.left)
    print(node.ip, node.bytes)
    if node.right:
        print_tree(node.right)
