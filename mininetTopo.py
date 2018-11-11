'''
Please add your name: Yap Han Chiang
Please add your matric number: A0125168E
'''

import os
import sys
import atexit
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.link import Link
from mininet.node import RemoteController

net = None

class TreeTopo(Topo):

    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        file = open('topology.in')

        [numHost, numSwitch, numLinks] = [int(x) for x in file.readline().split(' ')]
        
        # Add hosts
        for i in range(numHost):
            self.addHost('h%d' % (i+1))

        # Add switches
        for i in range(numSwitch):
            sconfig = {'dpid': "%016x" % (i+1)}
            self.addSwitch('s%d' % (i+1), **sconfig)

        # Add links
        for line in file:
            [node1, node2, bw] = line.split(',')
            self.addLink(node1, node2, int(bw))
        
        file.close()

def startNetwork():
    info('** Creating the tree network\n')
    topo = TreeTopo()

    global net
    net = Mininet(topo=topo, link = Link,
            controller=lambda name: RemoteController(name, ip='192.168.56.1'),
            listenPort=6633, autoSetMacs=True)

    info('** Starting the network\n')
    net.start()

    #  Create QoS Queues
    # > os.system('sudo ovs-vsctl -- set Port [INTERFACE] qos=@newqos \
    #            -- --id=@newqos create QoS type=linux-htb other-config:max-rate=[LINK SPEED] queues=0=@q0,1=@q1,2=@q2 \
    #            -- --id=@q0 create queue other-config:max-rate=[LINK SPEED] other-config:min-rate=[LINK SPEED] \
    #            -- --id=@q1 create queue other-config:min-rate=[X] \
    #            -- --id=@q2 create queue other-config:max-rate=[Y]')

    info('** Running CLI\n')
    CLI(net)

def stopNetwork():
    if net is not None:
        net.stop()
    # Remove QoS and Queues
    os.system('sudo ovs-vsctl --all destroy Qos')
    os.system('sudo ovs-vsctl --all destroy Queue')


if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
