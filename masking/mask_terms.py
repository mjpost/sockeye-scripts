#!/usr/bin/env python3
# -*- coding: iso8859-1 -*-
import argparse
import json
import logging
import os
import re
import sys

from collections import defaultdict, namedtuple
from typing import List, Optional


def is_comment_or_empty(s: str) -> str:
    return s.startswith('#') or re.search(r'^\s*$', s)


def get_mask(label, index: Optional[int] = None):
    """
    Produces a maybe-indexed mask.
    """
    if index is None:
        return '__{}__'.format(label)
    else:
        return '__{},{}__'.format(label, index)

def singlespace(s: str) -> str:
    if s is not None:
        s = re.sub(r' +', ' ', s.strip())
    return s


class TermMasker:
    def __init__(self,
                 pattern_files: List[str],
                 term_files: List[str],
                 add_index: Optional[bool] = False) -> None:

        self.patterns = []
        self.terms = {}
        self.add_index = add_index

        for file in pattern_files:
            self.load_patterns(file)
        for file in term_files:
            self.load_terms(file)

        self.counts = defaultdict(int)
        self.counts_missed = defaultdict(int)
        self.counts_dupes = defaultdict(int)

        self.mask_matcher = re.compile(r'^__[A-Z][A-Z0-9_]*,\d+__$')

    def load_terms(self, file: str):
        with open(file) as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                term, translation, label = line.rstrip().split('|||')
                term = term.strip()
                translation = translation.strip()
                label = label.strip()
                if term in self.terms:
                    self.counts_dupes[term] += term
                else:
                    self.terms[term] = (translation, label)

    def load_patterns(self, file: str):
        with open(file) as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                pattern, label = line.rstrip().split('|||')
                pattern = pattern.strip()
                label = label.strip()
                pattern = ' ' + pattern + ' '
                self.patterns.append((pattern, label))

    def unmask(self, output, orig_source, masked_source):
        """
        Removes masks.

        orig_source: The boy is 10
        masked_source: The boy is __NUM,1__
        output: Le garçon est __NUM,1__

        mask2word: { '__NUM,1__': '10' }

        """
        # Create a dictionary mapping indexed masks to their corresponding unmasked source words
        mask2word = dict(filter(lambda x: self.mask_matcher.match(x[0]), zip(masked_source.split(), orig_source.split())))

        # Replace these in the string one by one
        output = ' '.join([mask2word.get(word, word) for word in output.split()])

        return output

    def mask(self, orig_source, orig_target: Optional[str] = None):
        source, target = self.mask_by_term(orig_source, orig_target)
        source, target = self.mask_by_pattern(source, target)
        return singlespace(source), singlespace(target)
    
    def mask_by_term(self, source, target: Optional[str] = None):
        # increment the indices to use
        indices = defaultdict(int)
        for term in self.terms:
            translation, label = self.terms[term]
            match = re.finditer(re.escape(term), source)
            for m in match:
                # if there is no target, or the string matches the target too
                tmatch = None
                if target is not None:
                    tmatch = re.search(re.escape(translation), target)
                if target is None or tmatch is not None:
                    indices[label] += 1
                    labelstr = get_mask(label, indices[label]) if self.add_index else get_mask(label)
                    labelstr = ' {} '.format(labelstr)

                    source = source.replace(m.group(), labelstr, 1)
                    if target is not None:
                        target = target.replace(tmatch.group(), labelstr, 1)
                    self.counts[label] += 1
                else:
                    self.counts_missed[label] += 1

        return source, target

    def mask_by_pattern(self, source, target: Optional[str] = None):
        # pad with spaces
        source = ' {} '.format(source).replace(' ', '  ')
        target = None if target is None else ' {} '.format(target)
        
        # increment the indices to use
        indices = defaultdict(int)
        for pattern, label in self.patterns:
            match = re.finditer(pattern, source)
            for m in match:
                # if there is no target, or the string matches the target too
                if target is None or m.group() in target:
                    indices[label] += 1
                    labelstr = get_mask(label, indices[label]) if self.add_index else get_mask(label)
                    labelstr = ' {} '.format(labelstr)

                    source = source.replace(m.group(), labelstr, 1)
                    if target is not None:
                        target = target.replace(m.group(), labelstr, 1)
                    self.counts[label] += 1
                else:
                    self.counts_missed[label] += 1

        return source, target

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pattern_files', '-p', nargs='+', type=str,
                        default=['{}/patterns.txt'.format(os.path.dirname(sys.argv[0]))],
                        help='List of files with patterns')
    parser.add_argument('--term_files', '-t', nargs='+', type=str,
                        default=['{}/dict.txt'.format(os.path.dirname(sys.argv[0]))],
                        help='List of files with terminology dictionaries')
    parser.add_argument('--add-index', '-i', action='store_true',
                        help='Add an index to each mask')
    parser.add_argument('--unmask', '-u', action='store_true',
                        help='Perform unmasking')
    parser.set_defaults(func=lambda _: parser.print_help())
    args = parser.parse_args()

    masker = TermMasker(args.pattern_files, args.term_files, add_index=args.add_index)

    for lineno, line in enumerate(sys.stdin, 1):
        line = line.rstrip('\n')

        if args.unmask:
            tokens = line.split('\t')
            if len(tokens) != 3:
                raise Exception('Need three fields (output, orig source, and masked source)!')

            # output, orig_source, masked_source
            unmasked = masker.unmask(*tokens)
            print(unmasked, flush=True)
        else:
            if '\t' in line:
                orig_source, orig_target = line.split('\t', 1)
            else:
                orig_source = line
                orig_target = None

                if args.unmask:
                    raise Exception()

            source, target = masker.mask(orig_source, orig_target)

            if target is None:
                print(source, flush=True)
            else:
                print(source, target, sep='\t', flush=True)


if __name__ == "__main__":
    main()
