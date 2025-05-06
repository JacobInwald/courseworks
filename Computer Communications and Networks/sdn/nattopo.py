from mininet.topo import Topo

class NatTopo( Topo ):
    def build( self ):
        "Create NAT topo."

        # Add hosts and switches
        host1 = self.addHost( 'h1', ip="10.0.1.100/24", defaultRoute = "via 10.0.1.1")
        host2 = self.addHost( 'h2', ip="10.0.2.100/24", defaultRoute = "via 10.0.2.1" )
        host3 = self.addHost( 'h3', ip="10.0.2.101/24", defaultRoute = "via 10.0.2.1" )
        switch = self.addSwitch( 's3' )

        # Add links
        self.addLink( host1, switch )
        self.addLink( switch, host2 )
        self.addLink( switch, host3 )
topos = { 'nattopo': ( lambda: NatTopo() ) }
