# Quick Traffic Analysis Tutorial

Traffic analysis is an essential task in operational networks for anomaly
detection, usage understanding and infrastructure planning, to name a few.
Packet trace captured is typically represented in the pcap format, and looks like following:
```
05:11:08.999770 IP 133.34.250.140.1194 > 24.26.253.176.39264: UDP, length 26
05:11:08.999770 IP 151.133.237.33.443 > 163.210.142.7.53299: Flags [.], seq 10220:11680, ack 1, win 83, length 1460
05:11:08.999772 IP 202.132.100.13.50026 > 52.141.212.244.443: Flags [.], ack 2242675521, win 1029, length 0
05:11:08.999803 IP 203.62.165.212 > 202.119.233.22: ICMP echo request, id 47487, seq 5353, length 12
```
This trace contains 4 packets.
The first column indicates the timestamp when the packets have been captured.
In the first packet, 133.34.250.140.1194 means the source IPv4 address and
port number are 133.34.250.140 and 1194, respectively, and 24.26.253.176.39264
represents the destination ones in the same format.

An IP address identifies the host computer (more precisely, its network interface)
, whereas a port number identifies the application process (the OS kernel in the
host executes one or more processes).
Port numbers below 1023 are typically used for their associated specific
application-level protocols (services).
For example, 443 is used for HTTPS (TLS) and 22 is used for SSH.
Therefore, sometimes we can guess the service associated with captured packets.

The first packet is sent over UDP, whereas the second packet is delivered
over TCP (not written, but the remaining format indicates so).
Since the fourth packet is an ICMP packet, no transport protocol is used (thus
no port number is shown).

An IPv4 address identifies a host, and a port number identifies an application
endpoint. Therefore, an end-to-end flow is uniquely identified by the tuple of
`<src_ip><dst_ip><dst_ip><dst_port>` for each transport protocol (both ends
of the flow must use the same transport protocol).
Multiple flows between the same pair of the hosts usually have the same IPv4
address pair, but have different port number pairs. The server-side port number often has a typical service associated; for example, 22 and 80 indicates ssh and http servers, respectively.

### IPv4 address representation and Python objects

IPv4 address is a 32bit integer, and usually represented as a dot-separated four decimals.
For example, 1010000000000000000000000001 in binary or 167772161 in decimal is 
represented as 10.0.0.1.
An IPv4 address consists of the network address and host address parts, and the netmask defines
the length of the network address that the most significant bits of the IPv4
address indicate. For example, for 10.0.0.1, if the netmask is 24 bits, we
usually represent the network address part by 10.0.0.0/24.
Let's try to get some intuition by manipulating the IPv4Address and IPv4Network
Python objects.
```
vagrant@ubuntu-jammy:~$ python3
Python 3.10.12 (main, Jan 17 2025, 14:35:34) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from ipaddress import ip_address, ip_network
>>> a = ip_address('10.0.0.1')
>>> a
IPv4Address('10.0.0.1')
>>> int(a)
167772161
>>> na = ip_network('10.0.0.0/24')
>>> na
IPv4Network('10.0.0.0/24')
>>> na.network_address
IPv4Address('10.0.0.0')
>>> na.netmask
IPv4Address('255.255.255.0')
```
We can compute the network address if we know the IPv4 address and the netmask
by giving the IPv4 address with the netmask with `strict=False` flag to
`ip_network()`:
```
>>> na = ip_network('10.0.171.2/24')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3.10/ipaddress.py", line 74, in ip_network
    return IPv4Network(address, strict)
  File "/usr/lib/python3.10/ipaddress.py", line 1530, in __init__
    raise ValueError('%s has host bits set' % self)
ValueError: 10.0.171.2/24 has host bits set
>>> na = ip_network('10.0.171.2/24', strict=False)
>>> na
IPv4Network('10.0.171.0/24')
>>> na = ip_network('10.0.171.2/23', strict=False)
>>> na
IPv4Network('10.0.170.0/23')
```
In the above example, notice that the network address changes depending on the
netmask.

An IPv4Address or IPv4Network object can be converted to string easily:
```
>>> str(na)
'10.0.0.0/24'
```
Please refer to the [Python3 official document](https://docs.python.org/3/library/ipaddress.html) for more details of IPv4 address objects.

### Reading a Pcap file with Scapy

We use [Scapy](https://scapy.readthedocs.io/en/latest/) tool to process the packet traces in the assignments.

First we need to install Scapy

```
sudo pip3 install pytest matplotlib scapy==2.5.0
```

Scapy offers `RawPcapReader()` to read a pcap file (it can be gzip-ed), and various packet representation objects, as we can see in the below:
```
vagrant@ubuntu-jammy:~$ python3
Python 3.10.12 (main, Jan 17 2025, 14:35:34) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from ipaddress import ip_address
>>> from scapy.utils import RawPcapReader
>>> from scapy.layers.l2 import Ether
>>> from scapy.layers.inet import IP, TCP
>>> pkts = [p for i, (p, m) in enumerate(RawPcapReader('202201031400p.pcap.gz')) if i < 10]
```
The last line creates a list of 10 packet objects. Let's take a look at the Ethernet, IPv4 and TCP header of the first packet:
```
>>> ether = Ether(pkts[1])
>>> ether
<Ether  dst=f0:7c:c7:11:70:54 src=64:f6:9d:19:6a:52 type=IPv4 |<IP  version=4 ihl=5 tos=0x0 len=40 id=0 flags=DF frag=0 ttl=55 proto=tcp chksum=0x5c10 src=222.64.82.155 dst=133.6.49.222 |<TCP  sport=28145 dport=telnet seq=2231680516 ack=0 dataofs=5 reserved=0 flags=R window=0 chksum=0x170f urgptr=0 |>>>
>>> ip = ether[IP]
>>> ip
<IP  version=4 ihl=5 tos=0x0 len=40 id=0 flags=DF frag=0 ttl=55 proto=tcp chksum=0x5c10 src=222.64.82.155 dst=133.6.49.222 |<TCP  sport=28145 dport=telnet seq=2231680516 ack=0 dataofs=5 reserved=0 flags=R window=0 chksum=0x170f urgptr=0 |>>
```
You can easily obtain the `IPv4Address` object from the string:
```
>>> from ipaddress import ip_address
>>> ip_address(ip.src)
IPv4Address('222.64.82.155')
```
Finally, let's inspect the TCP header.
```
>>> tcp = ip[TCP]
>>> tcp
<TCP  sport=28145 dport=telnet seq=2231680516 ack=0 dataofs=5 reserved=0 flags=R window=0 chksum=0x170f urgptr=0 |>
>>> tcp.sport
28145
```

That's it, let's move on to the assignments in [README.md](./README.md). Internet measurement has been an important research topic. You can find interesting papers at [IMC](http://www.sigcomm.org/events/imc-conference) and [SIGCOMM](http://sigcomm.org/events/sigcomm-conference).
