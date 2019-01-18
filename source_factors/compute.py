#!/usr/bin/env python3
# *-* coding: utf-8 *-*

"""
Takes tokenized input and computes the subword representation, as well as any requested
factors, which are broadcast across the subwords.
"""
import argparse
import json
import sys

from abc import ABC, abstractmethod

from broadcast import broadcast
from factors import CaseFactor, SubwordFactor
from typing import Iterable, List, Generator

#from . import factors

class Subwordenizer(ABC):
    """
    Generic class for providing subword segmentation.
    This base class does nothing.
    """
    def __init__(self):
        pass

    def segment(self, line: str) -> str:
        return line

class BPE(Subwordenizer):
    def __init__(self, model_path):
        from subword_nmt import apply_bpe
        self.model = apply_bpe.BPE(model_path)

    def segment(self, sentence) -> str:
        pass


class SentencePiece(Subwordenizer):
    def __init__(self, model_path):
        import sentencepiece as spm
        self.model = spm.SentencePieceProcessor()
        self.model.Load(model)

    def segment(self, sentence):
        pass
        

def get_subwordenizer(method, model_path):
    if method == 'bpe':
        return BPE(model_path)
    elif method == 'sentencepiece':
        return SentencePiece(model_path)
    else:
        return Subwordenizer()


def main(args):

    subwordenizer = None

    factors = []
    for factor in args.factors:
        if factor == 'case':
            factors.append(CaseFactor())
        elif factor == 'subword':
            factors.append(SubwordFactor())
            subwordenizer = get_subwordenizer(args.subword_type, args.subword_model)

    for lineno, line in enumerate(args.input, 1):
        jobj = json.loads(line)

        if subwordenizer is not None:
            jobj['text'] = jobj['subword'] = subwordenizer.segment(jobj['text'])
            
        factor_names = args.factors
        factors = dict(zip(factor_names, [f.compute(jobj) for f in factors]))

        jobj['factor_names'] = factor_names
        jobj['factors'] = [factors[f] for f in factor_names]

        if subwordenizer is not None:
            jobj['factors'] = broadcast(factors['subword'], jobj['factors'])

        print(json.dumps(jobj, ensure_ascii=False), file=args.output, flush=True)


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
    params.add_argument('--subword-type', '-s',
                        choices=['bpe', 'sentencepiece', 'none'],
                        default='none')
    params.add_argument('--subword-model', '-m', 
                        default=None,
                        type=str,
                        help='Path to the subword model.')
    params.add_argument('--json', action='store_true',
                        help='Work with JSON input and output.')
    args = params.parse_args()

    main(args)
