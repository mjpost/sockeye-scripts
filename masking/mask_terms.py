#!/usr/bin/env python3
import argparse
import json
import logging
import os
#import re
import regex as re
import sys

from collections import defaultdict, namedtuple
from typing import List, Optional


def is_comment_or_empty(s: str) -> str:
    return s.startswith('#') or re.search(r'^\s*$', s)


#def get_mask(label, index: Optional[int] = None):
#    """
#    Produces a maybe-indexed mask.
#    """
#    if index is None:
#        return '__{}__'.format(label)
#    else:
#        return '__{},{}__'.format(label, index)

def singlespace(s: str) -> str:
    if s is not None:
        #s = regex.sub(r' +', ' ', s.strip())
        s = re.sub(r' +', ' ', s.strip())
    return s


class TermMasker:
    def __init__(self,
                 pattern_files: List[str],
                 dict_files: List[str],
                 add_index: Optional[bool] = False,
                 plabel_override: Optional[str] = None,
                 dlabel_override: Optional[str] = None) -> None:

        self.patterns = []
        self.terms = {}
        
        self.add_index = add_index
        
        self.default_label = "MASK"
        
        for file in pattern_files:
            self.load_patterns(file, plabel_override)
        
        for file in dict_files:
            self.load_terms(file, dlabel_override)

        self.counts = defaultdict(int)
        self.counts_missed = defaultdict(int)
        self.counts_dupes = defaultdict(int)

        #self.mask_matcher = regex.compile(r'^__[A-Z][A-Z0-9_]*,\d+__$')
        self.mask_matcher = re.compile(r'^__[A-Z][A-Z0-9_]*,\d+__$')

    def load_terms(self, file: str, label_override: Optional[str] = None):
        with open(file) as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                elements = line.rstrip().split('|||')
                if len(elements) < 2:
                    # TODO: add error logging
                    continue
                term = elements[0].strip()
                translation = elements[1].strip()
                if label_override:
                    label = label_override
                elif len(elements) < 3:
                    label = self.default_label
                else:
                    label = elements[2].strip()
                    
                if term in self.terms:
                    self.counts_dupes[term] += term
                else:
                    self.terms[term] = (translation, label)

    def load_patterns(self, file: str, label_override: Optional[str] = None):
        with open(file) as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                elements = line.rstrip().split('|||')
                if len(elements) < 1:
                    # TODO: add error logging
                    continue
                pattern = elements[0].strip()
                if label_override:
                    label = label_override
                elif len(elements) < 2:
                    label = self.default_label
                else:
                    label = elements[1].strip()
                
                # Boundary checking also needs to be handled in the patterns themselves
                # because the behavior is different with word/non-word characters
                # on the edges!
                #pattern = ' ' + pattern + ' ' 
                self.patterns.append((pattern, label))

    def get_mask_string(self, label, index: Optional[int] = None):
        """
        Produces a maybe-indexed mask.
        """
        if index is None:
            return ' __{}__ '.format(label)
        else:
            return ' __{},{}__ '.format(label, index)
    
    def unmask(self, output, masks):
        """
        Removes masks.

        """
        unmasked = output
        for mask in masks:
            maskstr = mask["maskstr"]
            #matched = mask["matched"]
            replacement = mask["replacement"]
            unmasked = unmasked.replace(maskstr,replacement)
        
        return unmasked

    def mask(self, orig_source, orig_target: Optional[str] = None):
        masked_source, masked_target, term_masks = self.mask_by_term(orig_source, orig_target)
        masked_source, masked_target, pattern_masks = self.mask_by_pattern(masked_source, masked_target)
        term_masks.extend(pattern_masks)
        if self.add_index:
            indices = defaultdict(int)
            for mask in term_masks:
                maskstr = mask["maskstr"]
                label = mask["maskstr"].replace('_','')
                indices[label] += 1
                indexed_label = self.get_mask_string(label, indices[label])
                mask["maskstr"] = indexed_label
                masked_source = masked_source.replace(maskstr,indexed_label,1)
                if masked_target:
                    masked_target = masked_target.replace(maskstr, indexed_label,1)
        return masked_source, masked_target, term_masks
    
    def get_label_masks(self, label, source_pattern, unmask_string, source, target: Optional[str] = None):
        masks = []
        source_matches = re.finditer(source_pattern, source)
        for source_match in source_matches:
            if unmask_string is None:
                unmask_string = source_match.group()
            target_match = None
            if target is not None:
                target_match = re.search(re.escape(unmask_string), target)
            
            if target is None or target_match is not None:
                # don't apply index to masks until after applying patterns because digits
                labelstr = self.get_mask_string(label)
                source = re.sub(source_pattern, labelstr, source, 1)
                mask = { "maskstr":labelstr, "matched":source_match.group(), "replacement":unmask_string}
                masks.append(mask)
                if target is not None:
                    target = re.sub(re.escape(unmask_string), labelstr, target, 1)
                self.counts[label] += 1
            else:
                self.counts_missed[label] += 1
        return source, target, masks
        
    def mask_by_term(self, orig_source, orig_target: Optional[str] = None):
        source_masks =[]
        source = orig_source
        target = orig_target
        for term in self.terms:
            translation, label = self.terms[term]
            source, target, term_masks = self.get_label_masks(label, re.escape(term), translation, source, target)
            source_masks.extend(term_masks)            
        return source, target, source_masks
    
    def mask_by_pattern(self, orig_source, orig_target: Optional[str] = None):
        source_masks = []
        source = orig_source
        target = orig_target
        for pattern, label in self.patterns:
            source, target, pattern_masks = self.get_label_masks(label, pattern, None, source, target)
            source_masks.extend(pattern_masks)
        return singlespace(source), singlespace(target), source_masks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pattern-files', '-p', nargs='+', type=str,
                        default=['{}/patterns.txt'.format(os.path.dirname(sys.argv[0]))],
                        help='List of files with patterns')
    parser.add_argument('--dict-files', '-d', nargs='+', type=str,
                        default=['{}/dict.txt'.format(os.path.dirname(sys.argv[0]))],
                        help='List of files with terminology')
    parser.add_argument('--pattern-label', '-l', type=str,
                        default=None,
                        help='List of files with patterns')
    parser.add_argument('--dict-label', '-t', type=str,
                        default=None,
                        help='List of files with terminology')
    parser.add_argument('--json', '-j', action='store_true',
                        help='JSON input and output')
    parser.add_argument('--add-index', '-i', action='store_true',
                        help='Add an index to each mask')
    parser.add_argument('--unmask', '-u', action='store_true',
                        help='Perform unmasking')
    parser.set_defaults(func=lambda _: parser.print_help())
    args = parser.parse_args()

    masker = TermMasker(args.pattern_files, args.dict_files, add_index=args.add_index, plabel_override=args.pattern_label, dlabel_override=args.dict_label)

    for lineno, line in enumerate(sys.stdin, 1):
        jobj = None
        if args.json:
            jobj = json.loads(line)
            line = jobj['text']
        else:
            line = line.rstrip('\n')

        if args.unmask:
            if not args.json:
                raise Exception('Unmasking requires json format')
            
            output = jobj['masked_output']
            masks = jobj['masks']
            unmasked = masker.unmask(output, masks)
            jobj['unmasked'] = unmasked
            print(json.dumps(jobj), flush=True)
            
        else:
            if '\t' in line:
                orig_source, orig_target = line.split('\t', 1)
            else:
                orig_source = line
                orig_target = None

            masked_source, masked_target, masks = masker.mask(orig_source, orig_target)

            if orig_target is None:
                if args.json:
                    jobj['masked_source'] = masked_source
                    jobj['masks'] = masks
                    print(json.dumps(jobj), flush=True)
                else:
                    print(masked_source, flush=True)
            else:
                print(masked_source, masked_target, sep='\t', flush=True)

if __name__ == "__main__":
    main()
