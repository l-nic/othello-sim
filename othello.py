#!/usr/bin/env python2

import argparse
import simpy

DEBUG = True

def print_debug(s):
    if DEBUG:
        print s

class OthelloMsgState(object):
    """This class represents the state that each host maintains when
       it processes an OthelloMapMsg and sends out new boards
    """
    def __init__(self, src_host_id, src_msg_id, msg_id, map_cnt):
        # who to send the result to once all responses arrive
        self.src_host_id = src_host_id
        # ID of the msg to send the response to
        self.src_msg_id = src_msg_id
        # ID of the msg that generated this state
        self.msg_id = msg_id
        # number of messages (i.e. boards) that were generated in response to processing msgID
        self.map_cnt = map_cnt
        # number of the responses that have arrived so far (incremented during the reduce phase)
        self.response_cnt = 0

class OthelloMapMsg(object):
    """This class represents an Othello map message (i.e. the boards
       that need to be mapped to hosts)
    """
    count = 0
    def __init__(self, max_depth, src_msg_id=0, src_host_id=None, cur_depth=0):
        # maximum depth into the game tree this map message should propagate
        self.max_depth = max_depth
        # ID of the msg that generated this msg
        self.src_msg_id = src_msg_id
        # ID of the host that generated this msg
        self.src_host_id = src_host_id
        # how deep into the game tree this msg currently is
        self.cur_depth = cur_depth
        # unique msg ID
        self.ID = OthelloMapMsg.count
        OthelloMapMsg.count += 1

    def __str__(self):
        return 'OthelloMapMsg: ID={}, max_depth={}, src_msg_id={}, src_host_id={}, cur_depth={}'.format(self.ID, self.max_depth, self.src_msg_id, self.src_host_id, self.cur_depth)

    def add_src(self, src):
        self.sources.append(src)

class OthelloReduceMsg(object):
    """This class represents an Othello reduce message"""
    count = 0
    def __init__(self, target_host_id, target_msg_id):
        # ID of the host that this msg should be sent to
        self.target_host_id = target_host_id
        # ID of the map msg for which this msg is a response to
        self.target_msg_id = target_msg_id
        # unique msg ID
        self.ID = OthelloReduceMsg.count
        OthelloReduceMsg.count += 1

    def __str__(self):
        return 'OthelloReduceMsg: ID={}, target_host_id={}, target_msg_id={}'.format(self.ID, self.target_host_id, self.target_msg_id)

class OthelloHost(object):
    """This class represents an Othello host"""
    count = 0
    def __init__(self, env, args, network):
        self.env = env
        self.args = args
        self.queue = simpy.Store(env)
        self.network = network
        self.ID = OthelloHost.count
        OthelloHost.count += 1
        self.env.process(self.start_rcv())
        self.msg_state = {}

    def start_rcv(self):
        """Start listening for incomming messages"""
        while True:
            msg = yield self.queue.get()
            print_debug('{}: Received msg at host {}:\n\t"{}"'.format(self.env.now, self.ID, str(msg)))
            if type(msg) == OthelloMapMsg:
                yield self.env.process(self.handle_map_msg(msg))
            elif type(msg) == OthelloReduceMsg:
                self.handle_reduce_msg(msg)
            else:
                print '{}: ERROR: Receive invalid msg at host {}:\n\t"{}"'.format(self.env.now, self.ID, str(msg))

    def handle_map_msg(self, msg):
        """Service the request (i.e. compute new boards) then send new
           boards back into the network.
        """
        # model the service time
        yield self.env.timeout(self.args.service)
        if msg.cur_depth == msg.max_depth:
            print_debug('{}: Host {} starting reduce phase'.format(self.env.now, self.ID))
            # time to start the reduce phase
            new_msg = OthelloReduceMsg(msg.src_host_id, msg.src_msg_id)
            # send msg into network (kick this off asynchronously cuz we don't want to model serialization)
            self.env.process(self.transmit_msg(new_msg))
        else:
            print_debug('{}: Host {} generating new map messages'.format(self.env.now, self.ID))
            # remember that we need to receive responses for this msg during the reduce phase
            self.msg_state[msg.ID] = OthelloMsgState(msg.src_host_id, msg.src_msg_id, msg.ID, self.args.branch)
            # compute new boards and send them back into the network
            for i in range(self.args.branch):
                new_msg = OthelloMapMsg(msg.max_depth, msg.ID, self.ID, msg.cur_depth+1)
                # send msg into network (kick this off asynchronously cuz we don't want to model serialization)
                self.env.process(self.transmit_msg(new_msg))

    def handle_reduce_msg(self, msg): 
        """Wait to receive all responses then forward result up the tree"""
        if msg.target_msg_id not in self.msg_state:
            print '{}: ERROR: host {} receive response for msg {} but does not have any state for this msg'.format(self.env.now, self.ID, msg.target_msg_id)
        state = self.msg_state[msg.target_msg_id]
        # update state / send result upstream
        state.response_cnt += 1
        if state.response_cnt == state.map_cnt:
            print_debug('{}: Host {} received all responses, sending result upstream'.format(self.env.now, self.ID))
            if state.src_host_id is None:
                print '{}: SIMULATION COMPLETE!'.format(self.env.now)
            else:
                # all responses have been received so send result upstream
                new_msg = OthelloReduceMsg(state.src_host_id, state.src_msg_id)
                self.env.process(self.transmit_msg(new_msg))

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
            print_debug('{}: Switching msg\n\t"{}"'.format(self.env.now, str(msg)))
            if type(msg) == OthelloMapMsg:
                # TODO: this isn't a very random hash function ... does it matter?
                dst = msg.ID % len(self.hosts)
            elif type(msg) == OthelloReduceMsg:
                dst = msg.target_host_id
            else:
                print '{}: ERROR: switch received unrecognized msg type: {}'.format(self.env.now, type(msg))
            # need to kick this off asynchronously so this is a non-blocking switch
            self.env.process(self.transmit_msg(msg, dst))

    def transmit_msg(self, msg, dst):
        # model the communication delay between switch and host
        yield self.env.timeout(self.args.delay)
        # put the message in the host's queue
        self.hosts[dst].queue.put(msg)

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
        init_msg = OthelloMapMsg(self.args.depth)
        self.hosts[0].queue.put(init_msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=int, help='Communication delay between network elements (ns)', default=1000)
    parser.add_argument('--service', type=int, help='Service time at each host (ns)', default=500)
    parser.add_argument('--hosts', type=int, help='Number of hosts to use in the simulation', default=7)
    parser.add_argument('--branch', type=int, help='Othello game tree branching factor', default=2)
    parser.add_argument('--depth', type=int, help='How deep to search into the game tree', default=2)
    args = parser.parse_args()

    # Setup and start the simulation
    print 'Running Othello Simulation ...'
    env = simpy.Environment()
    
    s = OthelloSimulator(env, args)

    env.run()

if __name__ == '__main__':
    main()
