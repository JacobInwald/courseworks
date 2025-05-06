import pytest
from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP
from ipaddress import ip_address, ip_network
from pcap_aggr import Data, Node
from ipaddress import ip_network

testfile = '202201031400p.pcap.gz'
testdata_aggr = {
'18.64.64.161/32': 19668641, '0.0.0.0/2': 13166557, '0.0.0.0/1': 12217011, '0.0.0.0/32': 16612739, '128.0.0.0/5': 11085227, '133.11.0.0/32': 21218842, '133.11.64.0/18': 10547432, '128.0.0.0/32': 13049195, '157.173.0.0/17': 10993550, '144.0.0.0/4': 11811368, '128.0.0.0/2': 10981894, '160.0.0.0/6': 11937114, '203.173.0.0/21': 17947522, '200.0.0.0/6': 24029952
}
testdata_aggr2 = {
'18.64.64.161/32': 19668641, '0.0.0.0/2': 13166557, '0.0.0.0/1': 12217011, '0.0.0.0/0': 16612739, '128.0.0.0/5': 13049195, '133.11.0.0/17': 21218842, '133.11.64.0/18': 10547432, '157.173.0.0/17': 10993550, '144.0.0.0/4': 11811368, '128.0.0.0/2': 10981894, '160.0.0.0/6': 11937114, '203.173.0.0/21': 17947522, '200.0.0.0/6': 24029952
}
output = None

def gotree(n):
    if n.left:
        assert int(n.ip) > int(n.left.ip)
        gotree(n.left)
    print(n)
    if n.right:
        assert int(n.ip) < int(n.right.ip)
        gotree(n.right)

def test_pcap_aggr1():
    root = None
    for pkt, _ in RawPcapReader(testfile):
        ether = Ether(pkt)
        if not 'type' in ether.fields:
            continue
        if ether.type != 0x0800:
            continue
        ip = ether[IP]
        if root is None:
            root = Node(ip_address(ip.src), ip.len)
        else:
            root.add(ip_address(ip.src), ip.len)
    gotree(root)

def test_pcap_aggr2():
    data = Data(testfile)
    tot = 0
    cor = 0
    for k, v in testdata_aggr.items():
        tot += 1
        if ip_network(k) in data.data:
            if data.data[ip_network(k)] == v:
                cor += 1
    assert cor/tot >= 0.5

def test_pcap_aggr3():
    if output:
        data = output
    else:
        data = Data(testfile)
    for k, v in testdata_aggr.items():
        if not ip_network(k) in data.data:
            break
        elif data.data[ip_network(k)] != v:
            break
    else:
        return
    for k, v in testdata_aggr2.items():
        assert data.data[ip_network(k)] == v
