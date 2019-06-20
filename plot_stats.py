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
        stats['time'], stats['qsize'] = parse_xy_samples(f)
        stats['avg_qsize'] = np.average(stats['qsize'])
        log_stats.append(stats)

    print 'Creating plots ...'

    # plot avg qsize time series
    f1 = plt.figure()
    for stats in log_stats:
        l = plt.plot(stats['time'], stats['qsize'], label=stats['label'], linestyle='-', marker='o')
        plt.axhline(y=stats['avg_qsize'], color=l[0].get_color(), label='{}-avg'.format(stats['label']), linestyle=':')
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

def plot_exp_avg_qsize(*files):
    # parse the sample files
    log_stats = []
    for f in files:
        stats = {}
        stats['label'] = os.path.basename(f).replace('.csv', '')
        stats['hostID'], stats['qsize'] = parse_xy_samples(f)
        stats['avg_qsize'] = np.average(stats['qsize'])
        log_stats.append(stats)

    print 'Creating plots ...'

    # plot expected avg qsize for each host
    f1 = plt.figure()
    for stats in log_stats:
        l = plt.plot(stats['hostID'], stats['qsize'], label=stats['label'], linestyle='-', marker='o')
        plt.axhline(y=stats['avg_qsize'], color=l[0].get_color(), label='{}-avg'.format(stats['label']), linestyle=':')
    plt.title("Expected Avg Queue Size For Each Host")
    plt.xlabel("Host ID")
    plt.ylabel("Avg Queue Size (messages)")
    plt.grid()
    plt.legend(loc='upper right')
    ax = plt.gca()
    ax.autoscale()

def plot_cpu_util(*files):
    # parse the sample files
    log_stats = []
    for f in files:
        stats = {}
        stats['label'] = os.path.basename(f).replace('.csv', '')
        stats['hostID'], stats['util'] = parse_xy_samples(f)
        log_stats.append(stats)

    print 'Creating plots ...'

    # plot expected avg qsize for each host
    f1 = plt.figure()
    for stats in log_stats:
        plt.plot(stats['hostID'], stats['util'], label=stats['label'], linestyle='-', marker='o')
    plt.title("Avg CPU Utilization For Each Host")
    plt.xlabel("Host ID")
    plt.ylabel("Avg CPU Utilization")
    plt.grid()
    plt.legend(loc='upper right')
    ax = plt.gca()
    ax.autoscale()

def plot_search_cdf(*files):
    # parse the sample files
    log_stats = []
    for f in files:
        stats = {}
        stats['label'] = os.path.basename(f).replace('.csv', '')
        stats['samples'] = parse_samples(f)
        log_stats.append(stats)

    print 'Creating plots ...'

    # plot CDF
    f1 = plt.figure()
    for stats in log_stats:
        plot_cdf(stats['samples'], stats['label'])
    plt.title("CDF of Othello search durations")
    plt.xlabel("Duration (ns)")
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

def plot_service_cdf(filename):
    # parse the sample files
    label  = os.path.basename(filename).replace('.txt', '')
    samples = parse_samples(filename)

    print 'Creating plots ...'

    # plot CDF of move counts
    f1 = plt.figure()
    plot_cdf(samples, label)
    plt.title("CDF of Othello 1-level search duration")
    plt.xlabel("Duration (ns)")
    plt.ylabel("CDF")
    plt.grid()
    plt.legend(loc='lower right')
    ax = plt.gca()
    ax.autoscale()

def plot_branch_cdf(filename):
    # parse the sample files
    label  = os.path.basename(filename).replace('.txt', '')
    samples = parse_samples(filename)

    print 'Creating plots ...'

    # plot CDF of move counts
    f1 = plt.figure()
    plot_cdf(samples, label)
    plt.title("CDF of Othello branching factor")
    plt.xlabel("Number of valid moves")
    plt.ylabel("CDF")
    plt.grid()
    plt.legend(loc='lower right')
    ax = plt.gca()
    ax.autoscale()

def plot_cdf(data, label):
    sortData = np.sort(data)
    yvals = np.arange(len(sortData))/float(len(sortData))
    plt.plot(sortData, yvals, label=label, linestyle='-', marker='o')

def parse_xy_samples(filename):
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
    parser.add_argument('--expAvgQsize', nargs='+', help='Files that contain expected avg qsize per host', required=False)
    parser.add_argument('--cpuUtil', nargs='+', help='Files that contain avg CPU utilization per host', required=False)
    parser.add_argument('--searchCDF', nargs='+', help='Files that contain search duration samples', required=False)
    parser.add_argument('--service', type=str, help='Files that contains service time samples', required=False)
    parser.add_argument('--branch', type=str, help='Files that contains branching factor samples', required=False)
    args = parser.parse_args()

    if args.avgQsize:
        plot_avg_qsize(*args.avgQsize)
    if args.allQsize:
        plot_qsize_cdf(*args.allQsize)
    if args.expAvgQsize:
        plot_exp_avg_qsize(*args.expAvgQsize)
    if args.cpuUtil:
        plot_cpu_util(*args.cpuUtil)
    if args.searchCDF:
        plot_search_cdf(*args.searchCDF)
    if args.service:
        plot_service_cdf(args.service)
    if args.branch:
        plot_branch_cdf(args.branch)

    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 32}
    matplotlib.rc('font', **font)
    plt.show()

if __name__ == '__main__':
    main()

