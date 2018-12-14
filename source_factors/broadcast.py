#!/usr/bin/env python3

"""
Takes a stream of BPE tokens and any number of streams of features computed over the
corresponding words, and broadcasts those features over the BPE tokens.
The inputs can be tab-delimited on STDIN, or in separate files.
Make sure that the BPE token string is the first column or file.
"""
import argparse
import sys
from typing import Iterable, List, Generator

UNK = '<unk>'
BPE_SUFFIX = '@@'

def compute_bpe(bpe_str: str) -> str:
    """
    Computes NER-style features for a BPE stream. e.g.,

    The boy ate the waff@@ le .
      O   O   O   O      B  E O

    The options are:
    O: a complete word
    B: beginning of a multi-token word
    I: interior of a multi-token word
    E: end of a multi-token word

    :param bpe_str: The BPE string.
    :return: A string of BPE factors.
    """
    factors = []
    was_in_bpe = False
    for i, token in enumerate(bpe_str.split()):
        now_in_bpe = token.endswith(BPE_SUFFIX)
        if was_in_bpe:
            if now_in_bpe:
                factor = 'I'
            else:
                factor = 'E'
        else:
            if now_in_bpe:
                factor = 'B'
            else:
                factor = 'O'

        was_in_bpe = now_in_bpe
        factors.append(factor)

    return ' '.join(factors)

def broadcast(bpe_str: str,
              input_factors: List[str],
              add_bpe: bool = False) -> List[str]:
    """
    Broadcasts factors computed on a segment over the corresponding BPE format of that segment.
    Applies to any number of input factors.
    Optionally also computes a BPE factor.
    Example:

    # original sentence (not present)
    The boy ate the waffles .
    # capitalization factor
    Cap lower lower lower lower -
    # BPE string (passed in)
    The boy at the waff@ les .
    # broadcasting
    Cap lower lower lower lower lower -

    :param bpe_str: The segment with BPE.
    :param input_factors: Any number of input factors as strings.
    :param add_bpe: Whether to prepend the BPE factor to the computed factors.
    :return: A list of factored strings
    """

    num_factors = len(input_factors)
    input_factors = [factor.split() for factor in input_factors]
    output_factors = [[] for f in range(num_factors)]
    if num_factors > 0:
        input_len = len(input_factors[0])
        token_i = 0
        for bpe_token in bpe_str.split():
            for i in range(num_factors):
                output_factors[i].append(input_factors[i][token_i] if token_i < input_len else UNK)

            if not bpe_token.endswith(BPE_SUFFIX):
                token_i += 1

    output_factors = [' '.join(factor) for factor in output_factors]

    if add_bpe:
        output_factors = [compute_bpe(bpe_str)] + output_factors

    return output_factors


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
    for lineno, (bpe_tokenstr, *factors) in enumerate(input_stream, 1):

        broadcast_factors = broadcast(bpe_tokenstr, factors, not args.no_bpe_factor)

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
    params.add_argument('--no-bpe-factor', action='store_true',
                        help='Do not output the BPE factor. Default: output it as the first factor.')
    args = params.parse_args()

    main(args)
