'''
Please add your name: Yap Han Chiang
Please add your matric number: A0125168E
'''

import sys
import os
from sets import Set

from pox.core import core

import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_tree

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        # Routing table for 4 switches: Dictionary of dictionary
        self.macToPort = {}

    # You can write other functions as you need.
        
    def _handle_PacketIn (self, event):    
        packet = event.parsed
        inPort = event.port

        dpid = event.dpid
        src = packet.src
        dst = packet.dst

    	# install entries to the route table
        def install_enqueue(event, packet, outport, q_id):
            pass
          

    	# Check the packet and decide how to route the packet
        def forward(message = None):
            log.debug("packet: %s, dpid: %s, src: %s, dst: %s, port: %s" %(packet, dpid, src, dst, port))

            if dst.is_multicast:
                flood()
            elif dst not in self.macToPort[dpid]:
                flood('Port for %s unknown -- flooding' % (dst)
            else:
                pass
                # outPort = self.macToPort[dpid][dst]
                # if outPort == inPort:
                    #log.warning('Same port for packet from %s -> %s on %s.%s. Drop' % (src, dst, dpid_to_str(dpid, outPort)))
    

        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
            pass
        
        
        forward()


    def _handle_ConnectionUp(self, event):
        dpid = dpid_to_str(event.dpid)
        log.debug("Switch %s has come up.", dpid)

        # Init routing table for each switch
        self.macToPort[dpid] = {}
        
        # Send the firewall policies to the switch
        def sendFirewallPolicy(connection, policy):
            pass
            

        # for i in [FIREWALL POLICIES]:
           # sendFirewallPolicy(event.connection, i)
            

def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_tree.launch()

    # Starting the controller module
    core.registerNew(Controller)
