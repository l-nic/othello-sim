#!/usr/bin/env python

import sys, os
import argparse
import numpy as np

def log_stats(levels, sample_files, pc, outfile):

    data = []
    for lvl, fname in zip(levels, sample_files):
        samples = parse_samples(fname)
        data.append((lvl, np.percentile(samples, pc)))

    outfile += '-{}p.csv'.format(pc)
    with open(outfile, 'w') as f:
        for p in data:
            f.write('{}, {}\n'.format(p[0], p[1]))

def parse_samples(filename):
    data = []
    with open(filename) as f:
        for line in f:
            try:
                data.append(float(line))
            except:
                print "ERROR: invalid line in file: {}".format(line)
    return data

def make_list(*args):
    return [a for a in args]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--levels', nargs='+', help='The level corresponding to each sample file', required=True)
    parser.add_argument('--samples', nargs='+', help='Files that contain all completion time samples', required=True)
    parser.add_argument('--outFile', type=str, help='Filename prefix to write the output', required=True)
    args = parser.parse_args()

    levels = make_list(*args.levels)
    sample_files = make_list(*args.samples)

    if len(levels) != len(sample_files):
        print  "ERROR: must provide the sample number of levels and sample files"
        return

    # create the output directory if it doesn't exist
    out_dir = os.path.join(os.getcwd(), os.path.dirname(args.outFile))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    log_stats(levels, sample_files, 50, args.outFile)
    log_stats(levels, sample_files, 99, args.outFile)

if __name__ == '__main__':
    main()

