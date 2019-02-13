#!/usr/bin/env python3

"""
Takes in tab-delimited triples of (combined score, source, target) and only prints lines above the threshold.
"""

import argparse
import math
import sys

def main(args):
    skipped = 0
    i = 0
    for i, line in enumerate(sys.stdin, 1):
        combined_score, source, target = line.rstrip().split('\t')
        combined_score = float(combined_score)

        if args.threshold != None and combined_score < args.threshold:
            skipped += 1
            continue

        print(combined_score, source, target, sep='\t', flush=True)

    if args.threshold != None:
        print('Skipped {} / {} lines at threshold {}'.format(skipped, i, args.threshold))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--threshold', '-t', type=float, default=None)
  args = parser.parse_args()
  main(args)
