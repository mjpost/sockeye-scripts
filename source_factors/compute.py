#!/usr/bin/env python3
# *-* coding: utf-8 *-*

"""
Takes tokenized input and computes the subword representation, as well as any requested
factors, which are broadcast across the subwords.
"""
import argparse
import json
import sys

from broadcast import broadcast
from factors import CaseFactor, SubwordFactor
from typing import Iterable, List, Generator

#from . import factors

def main(args):

    factors = []
    for factor in args.factors:
        if factor == 'case':
            factors.append(CaseFactor())
        elif factor == 'subword':
            factors.append(SubwordFactor())
        else:
            raise Exception('No such factor "{}"'.format(factor))

    factor_names = args.factors

    for lineno, line in enumerate(args.input, 1):
        if args.json:
            """
            This mode is used at inference time.
            Each factor knows the field it wants and picks it out of the JSON object.
            """
            jobj = json.loads(line)

            factors = dict(zip(factor_names, [f.compute_json(jobj) for f in factors]))

            jobj['factor_names'] = factor_names
            jobj['factors'] = [factors[f] for f in factor_names]

            if 'subword' in factors:
                jobj['factors'] = broadcast(factors['subword'], list(filter(lambda x: x != 'subword', jobj['factors'])))

            print(json.dumps(jobj, ensure_ascii=False), file=args.output, flush=True)
        else:
            """
            Used at training time.
            This script is called once for each feature, with the information it needs as raw text.
            """
            factor_str = factors[0].compute(line)
            print(factor_str, file=args.output)


if __name__ == '__main__':
    params = argparse.ArgumentParser(description='Compute factors over a token stream, then applies optional casing and subword processing.')
    params.add_argument('--input', '-i',
                        default=sys.stdin,
                        type=argparse.FileType('r'),
                        help='File stream to read tokenized data from. Default: STDIN.')
    params.add_argument('--output', '-o',
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Output file to write to. Default: STDOUT.')
    params.add_argument('factors',
                        nargs='+',
                        default=[],
                        help="List of factors to compute.")
    params.add_argument('--json', action='store_true',
                        help='Work with JSON input and output (inference mode).')

    args = params.parse_args()

    main(args)
