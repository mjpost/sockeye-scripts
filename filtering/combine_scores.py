#!/usr/bin/env python3

import argparse
import math
import sys

def main(args):
    skipped = 0
    i = 0
    for i, line in enumerate(sys.stdin, 1):
        tokens = line.rstrip().split('\t')
        if len(tokens) == 4:
            score1, score2, source, target = tokens
            score1 = float(score1)
            score2 = float(score2)
        elif len(tokens) == 2:
            score1, score2 = map(float, tokens)
            source = target = None
        else:
            print("Need either two or four fields!", file=sys.stderr)
            sys.exit(1)

        score = math.exp(-(abs(score1 - score2) + 0.5 * (score1 + score2)))

        if source is not None:
            print(score, source, target, sep='\t', flush=True)
        else:
            print(score, flush=True)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  args = parser.parse_args()
  main(args)
