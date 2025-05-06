from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from os_ken.controller.handler import set_ev_cls
from os_ken.ofproto import ofproto_v1_4
from os_ken.lib.packet import packet
from os_ken.lib.packet import ethernet
from os_ken.lib.packet import arp
from os_ken.lib.packet import ipv4
from os_ken.lib.packet import tcp
from os_ken.lib.packet.tcp import TCP_SYN, TCP_FIN, TCP_RST, TCP_ACK
from os_ken.lib.packet.ether_types import ETH_TYPE_IP, ETH_TYPE_ARP

class Nat(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Nat, self).__init__(*args, **kwargs)
        
        # Known host MAC addresses (unused in translation but available)
        self.hostmacs = {
            '10.0.1.100': '00:00:00:00:00:01',
            '10.0.2.100': '00:00:00:00:00:02',
            '10.0.2.101': '00:00:00:00:00:03',
        }
      
        self.public_ip = "10.0.1.2" # Set the NAT public IP
        self.lmac = "00:00:00:00:00:10"  # Private network interface (other ports)
        self.emac = "00:00:00:00:00:20"  # Public network interface (port 1)

        self.nat_table = {} # NAT table: key is tuple (priv_ip, priv_prt, dst_ip, dst_prt)
        self.max_entries = 65000 # max nat entries
        self.next_public_port = 1 # Next available public port number (starting from 1) 
        self.timeout = 10 # timeout in secs

        self.logger.info("INFO: Initialising controller ...")


    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=data
        )
        self.logger.info("INFO: Sent packet")
        return out


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        acts = [psr.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, psr.OFPMatch(), acts)


    def add_flow(self, dp, prio, match, acts, buffer_id=None, delete=False, timeout=None):
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        bid = buffer_id if buffer_id is not None else ofp.OFP_NO_BUFFER
        if delete:
            mod = psr.OFPFlowMod(datapath=dp, command=dp.ofproto.OFPFC_DELETE,
                    out_port=dp.ofproto.OFPP_ANY, out_group=dp.ofproto.OFPG_ANY,
                    match=match)
        else:
            ins = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acts)]
            if timeout:
                mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
                                match=match, instructions=ins, idle_timeout=timeout,
                                flags=ofp.OFPFF_SEND_FLOW_REM)
            else:
                mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
                                match=match, instructions=ins,
                                flags=ofp.OFPFF_SEND_FLOW_REM)

        dp.send_msg(mod)
        self.logger.info("INFO: Adding flow: match=%s actions=%s" % (match, acts))


    def send_rst(self, dp, in_port, eth, ip_pkt, tcp_pkt):
        '''
        Create a RST packet to inform the client that the connection is rejected.
        '''
        # Construct component packets
        new_eth = ethernet.ethernet(dst=eth.src, src=self.lmac, ethertype=eth.ethertype)
        new_ip = ipv4.ipv4(src=ip_pkt.dst, dst=ip_pkt.src, proto=ip_pkt.proto)
        new_tcp = tcp.tcp(
            src_port=tcp_pkt.dst_port,
            dst_port=tcp_pkt.src_port,
            bits=TCP_RST,
        )

        # Construct packet 
        rst_pkt = packet.Packet()
        rst_pkt.add_protocol(new_eth)
        rst_pkt.add_protocol(new_ip)
        rst_pkt.add_protocol(new_tcp)
        rst_pkt.serialize()

        # Send packet
        out = self._send_packet(dp, in_port, rst_pkt)
        dp.send_msg(out)
        self.logger.info("INFO: Sent RST packet: dst=%s dprt=%s" % (new_ip.dst, new_tcp.dst_port))
   

    #  -------------- NAT HELPERS ------------------

    def get_entry(self, key, inbound):
        '''
        Search NAT table for entry. This changes based on direction of packet.
        Return None if no entry found.
        '''
        # TODO: are inbound packets allowed to refresh the entry?
        #   right now the inbound packets don't refresh entries
        if inbound: # inbound packets are searched by port number
            entry, key = next(((e, k) for k, e in self.nat_table.items() \
                            if e['public_port'] == key[3] # search by public port  
                            and not e['expired']) # do not reinstate expired entries
                            , (None, None)) # return default as None
        else: # outbound packets are searched by connection 
            entry = self.nat_table.get(key, None)
        
        if entry:
            self.nat_table[key]['expired'] = False
         
        return entry, key


    def add_entry(self, key, in_port):
        '''
        Add entry to NAT table, removes old entry first and uses that
        '''
        if in_port == 1: # can't add entry for inbound traffic
            return None

        public_port = -1
        src_ip, src_port, _, _ = key 
        
        # Remove most recent expired port 
        exp_key = next((k for k, e in self.nat_table.items() \
                                    if e['expired']), None)
        if exp_key:
            entry = self.nat_table.pop(exp_key)
            public_port = entry['public_port']
            self.logger.info("INFO: Popped NAT table entry")
        
        # Check if table is full
        if len(self.nat_table) >= self.max_entries:
            self.logger.info("INFO: NAT table full")
            return
        
        # Advance public port, and wrap if greater than allowed TCP connections
        if public_port < 0: 
            public_port = self.next_public_port
            self.next_public_port = (self.next_public_port % 65535) + 1
        
        # Generate entry
        entry = {
            'public_port': public_port,
            'expired': False,
            'private_ip': src_ip, 
            'private_port': src_port, 
            'in_port': in_port
        }
        
        # Update NAT table
        self.nat_table[key] = entry
        self.logger.info('INFO: NAT table updated. entry=%s' % (entry.__str__()))
        return entry 

    
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        '''
        When flow is removed from flow table, we mark it expired in the NAT table, 
        using the flow's idle timeout as the actual timeout, to avoid syncing issues. 
        '''
        try: # prevents problems
            m = ev.msg.match 
            if m['in_port'] != 1: # outbound flows
                key = (m['ipv4_src'], m['tcp_src'], \
                        m['ipv4_dst'], m['tcp_dst'])
                _, key = self.get_entry(key, False)
            else:   # inbound flows
                _, key = self.get_entry((None, None, None, m['tcp_dst']), True)
            self.nat_table[key]['expired'] = True # mark expired
            self.logger.info(f"INFO: Flow {key} expired, and marked expired in table.")
        except Exception:
            self.logger.warning("WARN: Exception while marking flow expired.") 


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        '''
        Packet in handler
        '''
        # Intialisation 
        msg = ev.msg
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        dp = msg.datapath
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        self.logger.info("")
        self.logger.info("------------------------")
        self.logger.info("INFO: Packet Intercepted")
        self.logger.info("------------------------")
    
        # ------ ARP Handling -------
        if eth.ethertype == ETH_TYPE_ARP:
            ah = pkt.get_protocols(arp.arp)[0]
            if ah.opcode == arp.ARP_REQUEST:
                print('INFO: ARP', pkt)
                ar = packet.Packet()
                ar.add_protocol(ethernet.ethernet(ethertype=eth.ethertype,
                    dst=eth.src,
                    src=self.emac if in_port == 1 else self.lmac))
                ar.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                    src_mac=self.emac if in_port == 1 else self.lmac,
                    dst_mac=ah.src_mac, src_ip=ah.dst_ip, dst_ip=ah.src_ip))
                out = self._send_packet(dp, in_port, ar)
                print('INFO: ARP Rep', ar)
                dp.send_msg(out)
            return

        # --- IP/TCP NAT Handling ---
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        inbound = in_port == 1
        
        if tcp_pkt is None: # For simplicity, drop non-TCP IP packets.
            self.logger.warning("WARN: Not TCP, dropping ...")
            return
        if ip_pkt is None:  # Drop none IPv4 TCP packets.
            self.logger.warning("WARN: No IPv4 header, dropping ...")
            return

        # Search NAT table  
        self.logger.info(f"INFO: {'Inbound' if inbound else 'Outbound'} TCP Packet.")
        key = (ip_pkt.src, tcp_pkt.src_port, ip_pkt.dst, tcp_pkt.dst_port)
        entry, _ = self.get_entry(key, inbound)
        
                
        if not entry:
            if inbound: # drop unknown connection
                self.logger.warning("WARN: No entry found, dropping inbound connection ...")
                return
            else: # add new connection
                entry = self.add_entry(key, in_port)
                if not entry: # catch any fall through for RST case
                    self.send_rst(dp, in_port, eth, ip_pkt, tcp_pkt)
                    return 
        
        self.logger.info("INFO: Entry found, translating packet ...")

        # Perform NAT
        if not inbound: # translate packet for outbound requests
            new_eth = ethernet.ethernet(
                 dst=self.hostmacs.get(ip_pkt.dst, eth.dst),
                 src=self.emac,
                 ethertype=eth.ethertype)
            ip_pkt.src = self.public_ip
            tcp_pkt.src_port = entry['public_port']
        else: # translate packet for inbound requests
            new_eth = ethernet.ethernet(
                 dst=self.hostmacs.get(entry['private_ip'], eth.dst),
                 src=self.lmac,
                 ethertype=eth.ethertype)
            ip_pkt.dst = entry['private_ip']
            tcp_pkt.dst_port = entry['private_port']
        
        # Rebuild packet with updated headers.
        ip_pkt.csum = 0
        tcp_pkt.csum = 0
        new_pkt = packet.Packet()
        new_pkt.add_protocol(new_eth)
        new_pkt.add_protocol(ip_pkt)
        new_pkt.add_protocol(tcp_pkt)
        new_pkt.serialize() # recalc checksums
        
        # Send Packet
        self.logger.info("INFO: Translated packet, sending packet ...")
        port = entry['in_port'] if inbound else 1
        out = self._send_packet(dp, port, new_pkt)
        dp.send_msg(out)

        # Install flow 
        self.logger.info("INFO: Sent packet, installing flow ...")
        port = entry['in_port'] if inbound else 1
        if not inbound:    # outbound
            match = psr.OFPMatch(
                eth_type=0x0800,  # Ethernet type for IP
                ip_proto=6,       # IP protocol for TCP
                ipv4_src=key[0],
                tcp_src=key[1],
                ipv4_dst=key[2],
                tcp_dst=key[3],
                in_port=in_port,
            )
            actions = [
                psr.OFPActionSetField(eth_src=self.emac),
                psr.OFPActionSetField(eth_dst=self.hostmacs.get(ip_pkt.dst, eth.dst)),
                psr.OFPActionSetField(ipv4_src=self.public_ip),
                psr.OFPActionSetField(tcp_src=entry['public_port']),
                psr.OFPActionOutput(1)
            ]
        else:
            match = psr.OFPMatch(
                eth_type=0x0800,      
                ip_proto=6,            
                ipv4_dst=self.public_ip,
                tcp_dst=entry['public_port'],
                in_port=in_port               
            )
            actions = [
                psr.OFPActionSetField(eth_src=self.lmac),
                psr.OFPActionSetField(eth_dst=self.hostmacs.get(entry['private_ip'], eth.dst)),
                psr.OFPActionSetField(ipv4_dst=entry['private_ip']),
                psr.OFPActionSetField(tcp_dst=entry['private_port']),
                psr.OFPActionOutput(entry['in_port'])
            ]

        self.add_flow(dp, 1, match, actions, timeout=self.timeout)
        self.logger.info("INFO: Done")


