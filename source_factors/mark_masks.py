#!/usr/bin/env python3

"""
Adds a binary flag to words that fit the source factors that look like masks.
e.g., plain masks:

  __EMAIL__

or indexed ones:

  __EMAIL,6__
"""
import argparse
import gzip
import re
import sys

from functools import partial
from .utils import smart_open

token_pattern = re.compile(r'__\w+(,\d+)?__')
def is_mask(token):
    """
    :return: True if the input string looks like a mask, False otherwise.
    """
    return re.match(token_pattern, token)

def mask_all(line):
    """
    :return: A string of flags of the same token-length as the input indicating whether each input word is a mask.
    """
    return ' '.join(['MASK' if is_mask(token) else 'not_mask' for token in line.split()])

def main(args):
    for line in args.input:
        print(mask_all(line.rstrip()), file=args.output, flush=True)


if __name__ == '__main__':
    params = argparse.ArgumentParser(description='Marks masked words.')
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
