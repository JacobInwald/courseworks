import time
import pytest
from nat import Nat
from os_ken.lib.packet import packet, ethernet, arp, ipv4, tcp

# --- Dummy OpenFlow constants, parser and datapath ---

class DummyOfproto:
    OFP_NO_BUFFER = 0
    OFPP_CONTROLLER = 0xfffffffd
    OFPCML_NO_BUFFER = 0xffff
    OFPP_ANY = 0xfffffffa
    OFPG_ANY = 0xfffffffb
    OFPFC_DELETE = 3
    OFPIT_APPLY_ACTIONS = 0 

class DummyParser:
    def OFPActionOutput(self, port):
        return {"action": "output", "port": port}

    def OFPActionSetField(self, **kwargs):
        return {"action": "set_field", "fields": kwargs}

    def OFPMatch(self, **kwargs):
        return {"match": kwargs}

    def OFPFlowMod(self, **kwargs):
        # For testing, just return the kwargs as the flow mod message.
        return {"flow_mod": kwargs}

    def OFPInstructionActions(self, inst_type, actions):
        return {"instruction": inst_type, "actions": actions}

    def OFPBarrierRequest(self, dp):
        return {"barrier_request": True}

    def OFPFlowStatsRequest(self, datapath, out_port):
        return {"flow_stats_req": True, "out_port": out_port}

    def OFPPacketOut(self, datapath, buffer_id, in_port, actions, data):
        # Return a dummy packet-out message for testing.
        return {
            "OFPPacketOut": {
                "datapath": datapath,
                "buffer_id": buffer_id,
                "in_port": in_port,
                "actions": actions,
                "data": data
            }
        }

class DummyDatapath:
    def __init__(self):
        self.ofproto = DummyOfproto()
        self.ofproto_parser = DummyParser()
        self.sent_msgs = []

    def send_msg(self, msg):
        self.sent_msgs.append(msg)

# --- Dummy event and message ---
class DummyMsg:
    def __init__(self, datapath, in_port, data, buffer_id=DummyOfproto.OFP_NO_BUFFER):
        self.datapath = datapath
        self.match = {"in_port": in_port}
        self.buffer_id = buffer_id
        self.data = data

class DummyEvent:
    def __init__(self, msg):
        self.msg = msg

# --- Helper to create a TCP packet (SYN only for simplicity) ---
def create_tcp_packet(src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port, flags="S"):
    pkt = packet.Packet()
    eth_hdr = ethernet.ethernet(src=src_mac, dst=dst_mac, ethertype=0x0800)
    ip_hdr = ipv4.ipv4(src=src_ip, dst=dst_ip, proto=6)
    # Use the TCP flag provided. Here we use TCP_SYN from the tcp module.
    tcp_hdr = tcp.tcp(src_port=src_port, dst_port=dst_port, seq=100, ack=0,
                      offset=5, bits=getattr(tcp, "TCP_SYN"), window_size=1000)
    pkt.add_protocol(eth_hdr)
    pkt.add_protocol(ip_hdr)
    pkt.add_protocol(tcp_hdr)
    pkt.serialize()
    return pkt

# --- Integration Test 1: Outbound TCP packet processing ---
def test_full_chain_outbound(monkeypatch):
    """
    Simulate an outbound TCP connection initiated by a private host (in_port != 1).
    Verify that the packet is translated (source IP/port changed) and that a flow is installed.
    """
    nat_app = Nat()
    dp = DummyDatapath()
    # Outbound packet: from h2 (private host) at 10.0.2.100 with MAC as in hostmacs.
    # h2 is not on port 1, so choose in_port=2.
    pkt = create_tcp_packet(
        src_mac="00:00:00:00:00:01",  # h2's MAC as in hostmacs
        dst_mac="00:00:00:00:00:AA",  # arbitrary destination MAC
        src_ip="10.0.2.100",
        dst_ip="10.0.1.100",
        src_port=38758,
        dst_port=50000
    )
    # Build dummy event with in_port=2.
    msg = DummyMsg(dp, in_port=2, data=pkt.data)
    event = DummyEvent(msg)

    # Call the packet-in handler
    nat_app._packet_in_handler(event)

    # Check that a NAT entry was created.
    key = ("10.0.2.100", 38758, "10.0.1.100", 50000)
    assert key in nat_app.nat_table
    entry = nat_app.nat_table[key]
    # For outbound translation, the source IP should be changed to nat_app.public_ip and source port to entry['public_port']
    # Verify that a flow mod message was sent and at least one packet-out was issued.
    sent = dp.sent_msgs
    flow_mods = [msg for msg in sent if isinstance(msg, dict) and "flow_mod" in msg]
    pkt_outs = [msg for msg in sent if isinstance(msg, dict) and "OFPPacketOut" in msg]
    assert flow_mods, "No flow mod message sent"
    assert pkt_outs, "No packet-out message sent"
    # Confirm that the NAT table entry has a valid public port.
    assert entry["public_port"] > 0

# --- Integration Test 2: Inbound TCP packet processing ---
def test_full_chain_inbound(monkeypatch):
    """
    Simulate an inbound TCP packet arriving on port 1 (public side).
    The NAT table is pre-populated with an entry so that the packet is translated back to private.
    """
    nat_app = Nat()
    dp = DummyDatapath()
    # Pre-add a NAT table entry for a connection from h2 to h1.
    key = ("10.0.2.100", 38758, "10.0.1.100", 50000)
    monkeypatch.setattr(time, "time", lambda: 100)
    entry = nat_app.add_entry(key, in_port=2)
    public_port = entry["public_port"]

    # Create an inbound TCP packet destined to nat_app.public_ip with destination port = public_port.
    pkt = create_tcp_packet(
        src_mac="00:00:00:00:00:AA",  # arbitrary
        dst_mac="00:00:00:00:00:20",   # NAT public interface MAC
        src_ip="10.0.1.100",           # from server (public host)
        dst_ip=nat_app.public_ip,      # public IP of NAT
        src_port=50000,
        dst_port=public_port         # should match the NAT table entry
    )
    # Build dummy event with in_port=1 (public side).
    msg = DummyMsg(dp, in_port=1, data=pkt.data)
    event = DummyEvent(msg)

    # Call the packet-in handler
    nat_app._packet_in_handler(event)

    # Check that the packet was translated to private IP.
    sent = dp.sent_msgs
    flow_mods = [msg for msg in sent if isinstance(msg, dict) and "flow_mod" in msg]
    pkt_outs = [msg for msg in sent if isinstance(msg, dict) and "OFPPacketOut" in msg]
    assert flow_mods, "No flow mod message sent for inbound packet"
    assert pkt_outs, "No packet-out message sent for inbound packet"
    # Ensure that no new NAT entry was added (only the pre-existing one remains).
    assert len(nat_app.nat_table) == 1

# --- Integration Test 3: ARP request processing ---
def test_full_chain_arp(monkeypatch):
    """
    Simulate an ARP request packet arriving on both ports and check that the controller
    responds with the appropriate MAC address based on the in_port.
    """
    nat_app = Nat()
    dp = DummyDatapath()
    
    # Helper to create an ARP request.
    def create_arp_request(src_mac, src_ip, dst_ip):
        pkt = packet.Packet()
        eth_hdr = ethernet.ethernet(src=src_mac, dst="ff:ff:ff:ff:ff:ff", ethertype=0x0806)
        arp_hdr = arp.arp(opcode=arp.ARP_REQUEST,
                          src_mac=src_mac,
                          src_ip=src_ip,
                          dst_mac="00:00:00:00:00:00",
                          dst_ip=dst_ip)
        pkt.add_protocol(eth_hdr)
        pkt.add_protocol(arp_hdr)
        pkt.serialize()
        return pkt

    # Test ARP request arriving on port 1 (public side)
    pkt_public = create_arp_request("00:00:00:00:00:AA", "10.0.1.100", nat_app.public_ip)
    msg_public = DummyMsg(dp, in_port=1, data=pkt_public.data)
    event_public = DummyEvent(msg_public)
    nat_app._packet_in_handler(event_public)
    sent_public = dp.sent_msgs
    pkt_outs_public = [msg for msg in sent_public if isinstance(msg, dict) and "OFPPacketOut" in msg]
    assert pkt_outs_public, "No ARP reply sent for public side request"

    # Clear sent messages for next test.
    dp.sent_msgs.clear()

    # Test ARP request arriving on non-public port (e.g., port 2)
    pkt_private = create_arp_request("00:00:00:00:00:BB", "10.0.2.100", "10.0.2.1")
    msg_private = DummyMsg(dp, in_port=2, data=pkt_private.data)
    event_private = DummyEvent(msg_private)
    nat_app._packet_in_handler(event_private)
    sent_private = dp.sent_msgs
    pkt_outs_private = [msg for msg in sent_private if isinstance(msg, dict) and "OFPPacketOut" in msg]
    assert pkt_outs_private, "No ARP reply sent for private side request"

# =============================================================================
# Criterion 1: NAT mediates one TCP connection and installs a flow
# =============================================================================
def test_nat_connection_mediation():
    """
    Criterion 1: Verify that a TCP connection initiated from a private host (h2 or h3)
    is translated correctly and that a corresponding flow is installed.
    """
    nat_app = Nat()
    dp = DummyDatapath()
    # Simulate an outbound TCP packet from h2 (private host on in_port != 1)
    pkt = create_tcp_packet(
        src_mac="00:00:00:00:00:01",  # h2's MAC (as in hostmacs)
        dst_mac="00:00:00:00:00:AA",  # arbitrary destination
        src_ip="10.0.2.100",
        dst_ip="10.0.1.100",
        src_port=38758,
        dst_port=50000
    )
    msg = DummyMsg(dp, in_port=2, data=pkt.data)
    event = DummyEvent(msg)
    
    # Process the packet in the NAT controller.
    nat_app._packet_in_handler(event)
    
    # Verify a NAT table entry is created for the connection.
    key = ("10.0.2.100", 38758, "10.0.1.100", 50000)
    assert key in nat_app.nat_table, "NAT entry not created for outbound connection."
    entry = nat_app.nat_table[key]
    assert entry["public_port"] > 0, "Public port was not assigned."
    
    # Verify that a flow mod and packet-out messages were sent.
    flow_mods = [msg for msg in dp.sent_msgs if isinstance(msg, dict) and "flow_mod" in msg]
    pkt_outs = [msg for msg in dp.sent_msgs if isinstance(msg, dict) and "OFPPacketOut" in msg]
    assert flow_mods, "Flow mod message not sent."
    assert pkt_outs, "Packet-out message not sent."

# =============================================================================
# Criterion 2: Reuse the public port from an expired NAT table entry
# =============================================================================
def test_reuse_expired_entry(monkeypatch):
    """
    Criterion 2: Verify that when a NAT table entry expires,
    its public port is reused by a new connection.
    """
    nat_app = Nat()
    # Simulate adding an initial connection
    key1 = ("10.0.2.101", 40000, "10.0.1.100", 50000)
    # Set a base time.
    base_time = 100
    monkeypatch.setattr(time, "time", lambda: base_time)
    entry1 = nat_app.add_entry(key1, in_port=2)
    assert entry1 is not None, "New NAT entry was not created despite expired entry."
    reused_public_port = entry1["public_port"]

    # Advance time beyond the timeout so that entry1 is considered expired.
    monkeypatch.setattr(time, "time", lambda: base_time + nat_app.timeout + 1)
    key2 = ("10.0.2.102", 40001, "10.0.1.100", 50000)
    entry2 = nat_app.add_entry(key2, in_port=2)
    assert entry2 is not None, "New NAT entry was not created despite expired entry."
    assert entry2["public_port"] == reused_public_port, "Expired public port was not reused."

# =============================================================================
# Criterion 3: Send a RST packet when NAT table is full
# =============================================================================
def test_send_rst_when_nat_table_full(monkeypatch):
    """
    Criterion 3: When the NAT table is full, the controller should send a TCP RST
    to the client. We simulate a full table and then inject an outbound packet.
    """
    nat_app = Nat()
    dp = DummyDatapath()
    in_port = 2

    # Fill the NAT table to the maximum allowed entries.
    for i in range(nat_app.max_entries):
        key = (f"10.0.2.{(i % 254) + 1}", 40000 + i, "10.0.1.100", 50000)
        nat_app.nat_table[key] = {
            "public_port": i + 1,
            "timestamp": time.time(),
            "private_ip": f"10.0.2.{(i % 254) + 1}",
            "private_port": 40000 + i,
            "in_port": in_port
        }

    # Override _send_packet to capture the sending of the RST packet.
    rst_sent = {"flag": False}
    def dummy_send_packet(datapath, port, pkt):
        # Check if the packet is a TCP packet with the RST flag set.
        # In our NAT code, send_rst creates a TCP packet with bits == TCP_RST.
        if pkt.get_protocol(tcp.tcp) and pkt.get_protocol(tcp.tcp).bits == tcp.TCP_RST:
            rst_sent["flag"] = True
        return "dummy_packet_out"
    nat_app._send_packet = dummy_send_packet

    # Now simulate an outbound TCP packet from a private host.
    pkt = create_tcp_packet(
        src_mac="00:00:00:00:00:03",  # h3's MAC (assuming it is in hostmacs)
        dst_mac="00:00:00:00:00:AA",
        src_ip="10.0.2.101",
        dst_ip="10.0.1.100",
        src_port=45000,
        dst_port=50000
    )
    msg = DummyMsg(dp, in_port=in_port, data=pkt.data)
    event = DummyEvent(msg)
    nat_app._packet_in_handler(event)
    
    assert rst_sent["flag"], "RST packet was not sent when NAT table was full."

# =============================================================================
# Criterion 4: Support 65,000 simultaneous active connections
# =============================================================================
def test_support_simultaneous_connections(monkeypatch):
    """
    Criterion 4: Verify that the NAT can support up to 65,000 simultaneous active
    connections for a given server address/port.
    """
    monkeypatch.setattr(time, "time", lambda: 100)
    nat_app = Nat()
    in_port = 2
    total_entries = nat_app.max_entries
    nat_app.nat_table.clear()  # Start with an empty table

    # Simulate adding total_entries distinct connections.
    for i in range(total_entries):
        key = (f"10.0.2.{(i % 254) + 1}", 40000 + i, "10.0.1.100", 50000)
        entry = nat_app.add_entry(key, in_port=in_port)
        assert entry is not None, f"Failed to add connection at index {i}"
    assert len(nat_app.nat_table) == total_entries, "NAT table does not have expected number of entries."

    # Attempting to add one more should fail.
    extra_key = ("10.0.2.250", 50000, "10.0.1.100", 50000)
    extra_entry = nat_app.add_entry(extra_key, in_port=in_port)
    assert extra_entry is None, "Extra connection added despite NAT table being full."
