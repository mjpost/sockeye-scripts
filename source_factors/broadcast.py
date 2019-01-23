#!/usr/bin/env python3
# *-* coding: utf-8 *-*

"""
Takes a stream of subword factors and any number of streams of features computed over the
corresponding words, and broadcasts those features over the subword features.
The inputs can be tab-delimited on STDIN, or in separate files.
***Make sure*** that the subword feature is the first column or file.
"""
import argparse
import sys
from typing import Iterable, List, Generator

UNK = '<unk>'

def broadcast(subword_factors: str,
              input_factors: List[str]) -> List[str]:
    """
    Broadcasts factors computed on a segment over the corresponding suword format of that segment.
    Does this for any number of input factors.
    The subword format is expected to be in the form of subword *features*: BIEO, where
    - B is the first subword token of a word
    - I is the interior, non-final subword token
    - E is the last subword token of a word
    - O is a stand-alone subword token

    Example:

    # original sentence (not present)
    The boy ate the waffles .
    # capitalization factor
    Cap lower lower lower lower -
    # BPE string (passed in)
    The boy at the waff@ les .
    # Corresponding subword factor string
    O O O O B E O
    # broadcasting
    Cap lower lower lower lower lower -

    :param subword_factors: The segment with BPE.
    :param input_factors: Any number of input factors as strings.
    :return: A list of factored strings
    """

    num_factors = len(input_factors)
    input_factors = [factor.rstrip().split() for factor in input_factors]
    output_factors = [[] for f in range(num_factors)]
    if num_factors > 0:
        input_len = len(input_factors[0])
        token_i = 0
        for subword_factor in subword_factors.split():
            for i in range(num_factors):
                output_factors[i].append(input_factors[i][token_i] if token_i < input_len else UNK)

            if subword_factor in ['E', 'O']:
                token_i += 1

    output_factors = [' '.join(factor) for factor in output_factors]

    return [subword_factors] + output_factors


def split_stream(stream: Iterable[str] = sys.stdin) -> Generator[List[str], None, None]:
    """
    Input can come as a separate list of files, or tab-delimited on STDIN.
    This takes a single stream and splits it on tab to handle the second case.

    :param stream: The input stream.
    :return: A generator over pairs of strings.
    """

    for line in stream:
        yield line.split('\t')


def main(args):
    input_stream = split_stream(sys.stdin) if args.inputs is None else zip(*args.inputs)
    for lineno, (subword_tokenstr, *factors) in enumerate(input_stream, 1):

        broadcast_factors = broadcast(subword_tokenstr.rstrip(), factors)

        print('\t'.join(broadcast_factors), file=args.output, flush=True)


if __name__ == '__main__':
    params = argparse.ArgumentParser(description='Projects token factors across subword tokens.')
    params.add_argument('--inputs', '-i',
                        nargs='+',
                        default=None,
                        type=argparse.FileType('r'),
                        help='Paths to factor files. The first is the BPE factors. Default: STDIN.')
    params.add_argument('--output', '-o',
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Output file to write to. Default: STDOUT.')
    args = params.parse_args()

    main(args)
