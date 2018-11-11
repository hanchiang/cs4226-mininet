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

# constants
IDLE_TIMEOUT = 5
HARD_TIMEOUT = 10

FIREWALL_PRIORITY = 100

class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        # Routing table for 4 switches: Dictionary of dictionary
        self.macToPort = {}

        # For premium plans
        self.premiumPlans = {}

        # You can write other functions as you need.

    def _handle_PacketIn(self, event):
        packet = event.parsed
        inport = event.port
        dpid = dpid_to_str(event.dpid)
        ofp = event.ofp

        src = packet.src
        dst = packet.dst

        # install entries to the route table
        def install_enqueue(outport, q_id):
            log.debug("Switch %s: Installing flow %s.%i -> %s.%i", dpid, src, inport, dst, outport)
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, inport)
            msg.idle_timeout = IDLE_TIMEOUT
            msg.hard_timeout = HARD_TIMEOUT
            msg.actions.append(of.ofp_action_output(port = outport))
            msg.data = ofp
            event.connection.send(msg)
            log.debug('Switch %s: Data sent to port %s', dpid, outport)

        # Check the packet and decide how to route the packet
        def forward(message=None):
            log.debug("packet: %s, dpid: %s, src: %s, dst: %s, port: %s" % (packet, dpid, src, dst, inport))
            if (src not in self.macToPort[dpid]):
                self.macToPort[dpid][src] = inport

            if dst.is_multicast:
                flood('Switch %s: multicast flood to port %s' % (dpid, dst))
            elif dst not in self.macToPort[dpid]:
                flood('Switch: %s, port for %s unknown -- flooding' % (dpid, dst))
            else:
                outport = self.macToPort[dpid][dst]
                install_enqueue(outport, 'random q') 

        # When it knows nothing about the destination, flood but don't install the rule
        def flood(message=None):
            log.debug(message)
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = ofp
            msg.in_port = inport
            event.connection.send(msg)
            log.debug('Sent message via port: %i' % of.OFPP_FLOOD)


        forward()
        log.debug('\n')


    def _handle_ConnectionUp(self, event):
        dpid=dpid_to_str(event.dpid)
        log.debug("Switch %s has come up.", dpid)

        # Init routing table and premium plan for each switch
        self.macToPort[dpid] = {}
        self.premiumPlans[dpid] = {}

        # firewall policies
        fwPolicies = []

        file = open('./pox/pox/misc/policy.in')
        [numFirewall, numPremium] = [int(x) for x in file.readline().split(' ')]

        # Send the firewall policies to the switch
        def sendFirewallPolicy(connection, policy):
            [fromHost, toHost, toPort] = policy

            msg = of.ofp_flow_mod()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))
            # match ipv4
            msg.match.dl_type = 0x800
            # 6 = tcp
            msg.match.nw_proto = 6
            msg.priority = FIREWALL_PRIORITY
            if (toHost and toPort):
                msg.match.nw_dst = toHost
                msg.match.tp_dst = toPort
                if (fromHost):
                    msg.match.nw_src = fromHost
            elif (fromHost and not toHost and not toPort):
                msg.match.nw_src = fromHost

            log.debug('Switch %s: Firewall rule for source host %s, dest host %s, dest port %s', dpid, fromHost, toHost, toPort)



        # Read in firewall policies
        for i in range(numFirewall):
            policy = file.readline().split(',')
            if len(policy) == 1:
                fwPolicies.append((policy[0], None, None))
            elif len(policy) == 2:
                fwPolicies.append((None, policy[0], policy[1]))
            elif len(policy) == 3:
                fwPolicies.append((policy[0], policy[1], policy[2]))
        
        # Read in premium hosts
        for i in range(numPremium):
            [host, plan] = file.readline().split(',')
            self.premiumPlans[dpid][host] = int(plan)
            log.debug('Switch %s: host %s is assigned plan %i', dpid, host, int(plan))

        for pol in fwPolicies:
           sendFirewallPolicy(event.connection, pol)


def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_tree.launch()

    # Starting the controller module
    core.registerNew(Controller)
