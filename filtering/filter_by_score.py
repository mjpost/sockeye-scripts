#!/usr/bin/env python3

import argparse
import math
import sys

def main(args):
    skipped = 0
    i = 0
    for i, line in enumerate(sys.stdin, 1):
        score1, score2, source, target = line.rstrip().split('\t')
        score1, score2 = float(score1), float(score2)

        score = -math.exp(abs(score1 - score2) + 0.5 * (score1 + score2))

        if args.threshold != None and score < args.threshold:
            skipped += 1
            continue
        print(score, score1, score2, source, target, sep='\t')

    if args.threshold != None:
        print('Skipped {} / {} lines at threshold {}'.format(skipped, i, args.threshold))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--threshold', '-t', type=float, default=None)
  args = parser.parse_args()
  main(args)
