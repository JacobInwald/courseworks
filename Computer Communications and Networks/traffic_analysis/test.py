import pcap_aggr as p
from ipaddress import ip_address

root = p.Node(ip_address("203.62.184.243"), 210)
data = [("209.243.136.123", 32), ("94.153.243.18", 40), ("150.10.10.225", 2277), ("146.121.1.156", 40), ("203.62.165.212", 64), ("202.132.97.10", 40), ("202.132.100.13", 40)]
data = [(ip_address(a), b) for a,b in data]
for i,j in data:
    root.add(i,j)

breakpoint()

root.aggr(137)
breakpoint()
p.print_tree(root)
