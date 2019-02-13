#!/usr/bin/env python3

import argparse
import math
import sys

def main(args):
    skipped = 0
    i = 0
    for i, line in enumerate(sys.stdin, 1):
        score1, score2 = map(float, line.rstrip().split('\t'))

        score = math.exp(-(abs(score1 - score2) + 0.5 * (score1 + score2)))

        print(score)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  args = parser.parse_args()
  main(args)
