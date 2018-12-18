#!/usr/bin/env python3

"""
Computes a case factor across tokens.
"""
import argparse
import gzip
import re
import sys

from functools import partial
from .utils import smart_open

def case(token):
    if token.isupper():
        return 'UPPER'
    elif token.istitle():
        return 'Title'
    elif token.islower():
        return 'lower'
    else:
        return '-'


def sentence_case(segment):
    return ' '.join(map(case, segment.split()))


def main(args):
    for line in args.input:
        print(sentence_case(line.rstrip()), file=args.output, flush=True)


if __name__ == '__main__':
    params = argparse.ArgumentParser(description='Computes case feature.')
    params.add_argument('--input', '-i',
                        type=smart_open,
                        default=sys.stdin,
                        help='Path to tokenized, cased input file. Default: STDIN.')
    params.add_argument('--output', '-o',
                        type=partial(smart_open, mode='w'),
                        default=sys.stdout,
                        help='Output file to write to. Default: STDOUT.')
    args = params.parse_args()

    main(args)
