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
        # store link bandwidth, because there is no other way to retrieve it!
        self.linkInfo = []
        for line in file:
            [node1, node2, bw] = line.split(',')
            self.addLink(node1, node2, int(bw))
            self.linkInfo.append(line)
        
        file.close()

# in bps
def getLinkSpeed(topo, node1, node2):
    for linkInfo in topo.linkInfo:
        [linkNode1, linkNode2, bw] = linkInfo.split(',')
        if (node1 == linkNode1 and node2 == linkNode2):
            # bw is in mbps
            return int(bw) * 1000000
    return 0

def createQoS(topo):
    print('Creating QoS...')
    for link in topo.links(True, False, True):
        [node1, node2, linkInfo] = link
        # linkInfo: A dict with keys node1, node2, port1, port2
        # print('node 1: %s, node 2: %s, linkinfo: %s' % (node1, node2, linkInfo))
        for switch in topo.switches():
            for i in [1, 2]:
                if (linkInfo['node%i' % i] == switch):
                    port = linkInfo['port%i' % i]
                    bw = getLinkSpeed(topo, node1, node2)
                    # W = premium tier lower bound guarantee
                    # Y = regular tier lower bound guarantee
                    # X = regular tier upper bound
                    # Z = free tier upper bound
                    W = 0.8 * bw
                    X = 0.6 * bw
                    Y = 0.3 * bw
                    Z = 0.2 * bw

                    #  Create QoS Queues
                    # Interface name is <switch>-eth<port>
                    # q0 = regular tier
                    # q1 = premium tier
                    # q2 = free tier
                    interface = '%s-eth%s' % (switch, port)
                    os.system('sudo ovs-vsctl -- set Port %s qos=@newqos \
                        -- --id=@newqos create QoS type=linux-htb other-config:max-rate=%i queues=0=@q0,1=@q1,2=@q2 \
                        -- --id=@q0 create queue other-config:max-rate=%i other-config:min-rate=%i \
                        -- --id=@q1 create queue other-config:min-rate=%i \
                        -- --id=@q2 create queue other-config:max-rate=%i' % (interface, bw, X, Y, W, Z))
    print('QoS created!')


def startNetwork():
    info('** Creating the tree network\n')
    topo = TreeTopo()

    global net
    net = Mininet(topo=topo, link = Link,
            controller=lambda name: RemoteController(name, ip='192.168.56.1'),
            listenPort=6633, autoSetMacs=True)

    info('** Starting the network\n')
    net.start()
    
    createQoS(topo)


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
