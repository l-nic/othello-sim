#!/usr/bin/env python

import sys, os
import matplotlib
import matplotlib.pyplot as plt
import argparse
import numpy as np

def plot_avg_qsize(*files):
    # parse the sample files
    log_stats = []
    for f in files:
        stats = {}
        stats['label'] = os.path.basename(f).replace('.csv', '')
        stats['time'], stats['qsize'] = parse_time_samples(f)
        log_stats.append(stats)

    print 'Creating plots ...'

    # plot avg qsize time series
    f1 = plt.figure()
    for stats in log_stats:
        plt.plot(stats['time'], stats['qsize'], label=stats['label'], linestyle='-', marker='o')
    plt.title("Time Series of Avg Host Queue Occupancy")
    plt.xlabel("Time (ns)")
    plt.ylabel("Queue Size (messages)")
    plt.grid()
    plt.legend(loc='upper right')
    ax = plt.gca()
    ax.autoscale()

def plot_qsize_cdf(*files):
    # parse the sample files
    log_stats = []
    for f in files:
        stats = {}
        stats['label'] = os.path.basename(f).replace('.csv', '')
        stats['samples'] = parse_samples(f)
        log_stats.append(stats)

    print 'Creating plots ...'

    # plot CDF of move counts
    f1 = plt.figure()
    for stats in log_stats:
        plot_cdf(stats['samples'], stats['label'])
    plt.title("CDF All queue size samples")
    plt.xlabel("Queue size (messages)")
    plt.ylabel("CDF")
    plt.grid()
    plt.legend(loc='lower right')
    ax = plt.gca()
    ax.autoscale()

    # print stats
    for stats in log_stats:
        print '{} Statistics:'.format(stats['label'])
        print '\t99% = {}'.format(np.percentile(stats['samples'], 99))
        print '\t50% = {}'.format(np.percentile(stats['samples'], 50))

def plot_cdf(data, label):
    sortData = np.sort(data)
    yvals = np.arange(len(sortData))/float(len(sortData))
    plt.plot(sortData, yvals, label=label, linestyle='-', marker='o')

def parse_time_samples(filename):
    time = []
    data = []
    with open(filename) as f:
        for line in f:
            try:
                t = float(line.split(',')[0])
                d = float(line.split(',')[1])
                time.append(t)
                data.append(d)
            except:
                print "ERROR: invalid line in file: {}".format(line)
    return time, data

def parse_samples(filename):
    data = []
    with open(filename) as f:
        for line in f:
            try:
                data.append(float(line))
            except:
                print "ERROR: invalid line in file: {}".format(line)
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--avgQsize', nargs='+', help='Files that contain avg queue size samples', required=False)
    parser.add_argument('--allQsize', nargs='+', help='Files that contain all queue size samples', required=False)
    args = parser.parse_args()

    if args.avgQsize:
        plot_avg_qsize(*args.avgQsize)
    if args.allQsize:
        plot_qsize_cdf(*args.allQsize)

    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 32}
    matplotlib.rc('font', **font)
    plt.show()

if __name__ == '__main__':
    main()
