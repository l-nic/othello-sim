#!/usr/bin/env python2

import argparse
import simpy

class OthelloMapMsg(object):
    """This class an Othello map message (i.e. the boards that need to be
       mapped to hosts)
    """
    count = 0
    def __init__(self, value, src):
        self.value = value
        self.src = src
        self.ID = OthelloMapMsg.count
        OthelloMapMsg.count += 1

class OthelloHost(object):
    """This class represents an Othello host"""
    count = 0
    def __init__(self, env, args, network):
        self.env = env
        self.args = args
        self.queue = simpy.Store(env)
        self.network = network
        self.hostID = OthelloHost.count
        OthelloHost.count += 1
        self.env.process(self.start_rcv())

    def start_rcv(self):
        """Start listening for incomming messages"""
        while True:
            msg = yield self.queue.get()
            print '{}: Received msg "{}" at host {} from host {}'.format(self.env.now, msg.value, self.hostID, msg.src)
            # model the service time
            yield self.env.timeout(self.args.service)

    def send(self, dst):
        msg = OthelloMessage("Hello There!!", self.hostID, dst)
        print '{}: Sending msg "{}" from host {} to host {}'.format(self.env.now, msg.value, self.hostID, msg.dst)
        # need to kick this off asynchronously cuz we don't want to model serialization
        self.env.process(self.transmit_msg(msg))

    def transmit_msg(self, msg):
        # model the communication delay
        yield self.env.timeout(self.args.delay)
        # put the message into the network queue
        self.network.put(msg)

class OthelloSwitch(object):
    """This class represents an Othello network switch"""
    def __init__(self, env, args):
        self.env = env
        self.args = args
        self.hosts = []
        self.queue = simpy.Store(env)
        self.env.process(self.start_switching())

    def add_hosts(self, hosts):
        self.hosts += hosts

    def start_switching(self):
        while True:
            msg = yield self.queue.get()
            print '{}: Switching msg "{}" to from host {} to host {}'.format(self.env.now, msg.value, msg.src, msg.dst)
            # need to kick this off asynchronously so this is a non-blocking switch
            self.env.process(self.transmit_msg(msg))

    def transmit_msg(self, msg):
        # model the communication delay between switch and host
        yield self.env.timeout(self.args.delay)
        # put the message in the host's queue
        self.hosts[msg.dst].queue.put(msg)

class OthelloSimulator(object):
    """This class controls the Othello simulation"""
    def __init__(self, env, args):
        self.env = env
        self.args = args
        self.hosts = []
        self.switch = OthelloSwitch(self.env, self.args)

        self.create_hosts()
        self.connect_hosts()
        
        self.init_sim()

    def create_hosts(self):
        for i in range(self.args.hosts):
            self.hosts.append(OthelloHost(self.env, self.args, self.switch.queue))

    def connect_hosts(self):
        """Connect hosts to switches"""
        self.switch.add_hosts(self.hosts)

    def init_sim(self):
        self.hosts[0].send(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=int, help='Communication delay between network elements (ns)', default=1000)
    parser.add_argument('--service', type=int, help='Service time at each host (ns)', default=500)
    parser.add_argument('--hosts', type=int, help='Number of hosts to use in the simulation', default=4)
    parser.add_argument('--branch', type=int, help='Othello game tree branching factor', default=3)
    args = parser.parse_args()

    # Setup and start the simulation
    print 'Running Othello Simulation ...'
    env = simpy.Environment()
    
    s = OthelloSimulator(env, args)

    env.run()

if __name__ == '__main__':
    main()
