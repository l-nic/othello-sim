#!/usr/bin/env python2

import argparse
import simpy
import numpy as np
import os

# np.random.seed(1)

#DEBUG = True
DEBUG = False

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

class OthelloMsg(object):
    """This is the base class for Othello messages"""
    def __init__(self, enq_time=0):
        self.enq_time = enq_time

class OthelloMapMsg(OthelloMsg):
    """This class represents an Othello map message (i.e. the boards
       that need to be mapped to hosts)
    """
    count = 0
    def __init__(self, max_depth, src_msg_id=0, src_host_id=None, cur_depth=0):
        super(OthelloMapMsg, self).__init__()
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

class OthelloReduceMsg(OthelloMsg):
    """This class represents an Othello reduce message"""
    count = 0
    def __init__(self, target_host_id, target_msg_id):
        super(OthelloReduceMsg, self).__init__()
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
    service_samples = []
    branch_samples = []
    def __init__(self, env, args, network):
        self.env = env
        self.args = args
        self.queue = simpy.Store(env)
        self.network = network
        self.ID = OthelloHost.count
        OthelloHost.count += 1
        self.env.process(self.start_rcv())
        self.msg_state = {}
        # count the number of messages this host pulled out of the queue
        self.msg_count = 0
        # count total queueing delay across all messages
        self.total_q_delay = 0
        # count time spent doing real work
        self.busy_time = 0

    def start_rcv(self):
        """Start listening for incomming messages"""
        while True:
            msg = yield self.queue.get()
            self.msg_count += 1
            self.total_q_delay += (self.env.now - msg.enq_time)
            print_debug('{}: Received msg at host {}:\n\t"{}"'.format(self.env.now, self.ID, str(msg)))
            if type(msg) == OthelloMapMsg:
                yield self.env.process(self.handle_map_msg(msg))
            elif type(msg) == OthelloReduceMsg:
                self.handle_reduce_msg(msg)
            else:
                print '{}: ERROR: Received invalid msg at host {}:\n\t"{}"'.format(self.env.now, self.ID, str(msg))

    def handle_map_msg(self, msg):
        """Service the request (i.e. compute new boards) then send new
           boards back into the network.
        """
        # model the service time
        service_time = np.random.choice(OthelloHost.service_samples)
        print_debug('{}: Host {} servicing request for {} ns'.format(self.env.now, self.ID, service_time))
        self.busy_time += service_time
        yield self.env.timeout(service_time)
        # only need to go to msg.max_depth-1 because the final machines will each look one more move ahead
        if msg.cur_depth == msg.max_depth-1:
            print_debug('{}: Host {} starting reduce phase'.format(self.env.now, self.ID))
            # time to start the reduce phase
            new_msg = OthelloReduceMsg(msg.src_host_id, msg.src_msg_id)
            # send msg into network 
            self.transmit_msg(new_msg)
        else:
            # pick how many new boards will be generated
            branch_factor = np.random.choice(OthelloHost.branch_samples)
            print_debug('{}: Host {} generating {} new map messages'.format(self.env.now, self.ID, branch_factor))
            # remember that we need to receive responses for this msg during the reduce phase
            self.msg_state[msg.ID] = OthelloMsgState(msg.src_host_id, msg.src_msg_id, msg.ID, branch_factor)
            # compute new boards and send them back into the network
            for i in range(branch_factor):
                new_msg = OthelloMapMsg(msg.max_depth, msg.ID, self.ID, msg.cur_depth+1)
                # send msg into network 
                self.transmit_msg(new_msg)

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
                OthelloSimulator.complete = True
                OthelloSimulator.finish_time = self.env.now
            else:
                # all responses have been received so send result upstream
                new_msg = OthelloReduceMsg(state.src_host_id, state.src_msg_id)
                self.transmit_msg(new_msg)

    def transmit_msg(self, msg):
        # put the message into the network queue
        self.network.put(msg)

    def report_avg_util(self):
        """Report avg CPU utilization. Should be invoked after the simulation completes"""
        return float(self.busy_time)/float(OthelloSimulator.finish_time)

    def report_exp_avg_qsize(self):
        """Report the expected avg queue size. Should be invoked after the simulation completes"""
        avg_arrival_rate = float(self.msg_count)/float(OthelloSimulator.finish_time)
        avg_qtime = float(self.total_q_delay)/float(self.msg_count)
        # compute avg qsize using Little's result
        return avg_arrival_rate*avg_qtime

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
                # This hashing function leads to perfect hashing if there is enough hosts
                dst = msg.ID % len(self.hosts)
            elif type(msg) == OthelloReduceMsg:
                dst = msg.target_host_id
            else:
                print '{}: ERROR: switch received unrecognized msg type: {}'.format(self.env.now, type(msg))
            # need to kick this off asynchronously so this is a non-blocking switch
            self.env.process(self.transmit_msg(msg, dst))

    def transmit_msg(self, msg, dst):
        # model the network communication delay
        yield self.env.timeout(self.args.delay)
        # put the message in the host's queue
        msg.enq_time = self.env.now
        self.hosts[dst].queue.put(msg)

class OthelloSimulator(object):
    """This class controls the Othello simulation"""
    complete = False
    finish_time = 0
    sample_period = 1000
    out_dir = 'out'
    def __init__(self, env, args):
        self.env = env
        self.args = args
        self.hosts = []
        self.switch = OthelloSwitch(self.env, self.args)

        self.create_hosts()
        self.connect_hosts()
        
        self.init_sim()

        self.avg_q_times = []
        self.avg_q_samples = []
        self.all_q_samples = []
        self.start_logging()

    def create_hosts(self):
        for i in range(self.args.hosts):
            self.hosts.append(OthelloHost(self.env, self.args, self.switch.queue))

    def connect_hosts(self):
        """Connect hosts to switches"""
        self.switch.add_hosts(self.hosts)

    def init_sim(self):
        init_msg = OthelloMapMsg(self.args.depth)
        self.hosts[0].queue.put(init_msg)

    def start_logging(self):
        self.env.process(self.print_progress())
        self.env.process(self.sample_host_queues())

    def print_progress(self):
        while not OthelloSimulator.complete:
            print '{}: Simulation running ...'.format(self.env.now)
            yield self.env.timeout(100000)

    def sample_host_queues(self):
        """Sample avg host queue occupancy at every time"""
        while not OthelloSimulator.complete:
            self.avg_q_times.append(self.env.now)
            q_samples = [len(h.queue.items) for h in self.hosts]
            self.avg_q_samples.append(np.average(q_samples))
            self.all_q_samples += q_samples
            yield self.env.timeout(OthelloSimulator.sample_period)
            
    def dump_logs(self):
        """Dump any logs recorded during the simulation"""
        out_dir = os.path.join(os.getcwd(), OthelloSimulator.out_dir)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # log the measured avg queue sizes
        with open(os.path.join(out_dir, 'avg_q_samples.csv'), 'w') as f:
            for t, q in zip(self.avg_q_times, self.avg_q_samples):
                f.write('{}, {}\n'.format(t, q))

        # log all queue size samples
        with open(os.path.join(out_dir, 'all_q_samples.csv'), 'w') as f:
            for q in self.all_q_samples:
                f.write('{}\n'.format(q))

        # log the expected long term avg queue occupancy per-host
        with open(os.path.join(out_dir, 'expected_avg_qsizes.csv'), 'w') as f:
            for h in self.hosts:
                f.write('{}, {}\n'.format(h.ID, h.report_exp_avg_qsize()))

        # log the average CPU utilization of each host
        with open(os.path.join(out_dir, 'cpu_utilization.csv'), 'w') as f:
            for h in self.hosts:
                f.write('{}, {}\n'.format(h.ID, h.report_avg_util()))

def parse_file(filename, data_type):
    """Simple helper function to parse samples from a file"""
    data = []
    with open(filename) as f:
        for line in f:
            try:
                data.append(data_type(line))
            except:
                print "ERROR: invalid line in file: {}".format(line)
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=int, help='Network communication delay (ns)', default=2000)
    parser.add_argument('--service', type=str, help='File that contains service time samples (ns)', default='dist/service-1000.txt') #'dist/1-level-search.txt')
    parser.add_argument('--branch', type=str, help='File that contains branch factor samples', default='dist/branch-5.txt') #'dist/move-count.txt')
    parser.add_argument('--hosts', type=int, help='Number of hosts to use in the simulation', default=1000)
    parser.add_argument('--depth', type=int, help='How deep to search into the game tree', default=8)
    args = parser.parse_args()

    # Setup and start the simulation
    OthelloHost.service_samples = parse_file(args.service, float)
    OthelloHost.branch_samples = parse_file(args.branch, int)
    print 'Running Othello Simulation ...'
    env = simpy.Environment() 
    s = OthelloSimulator(env, args)
    env.run()

    # dump simualtion logs
    s.dump_logs()

if __name__ == '__main__':
    main()
