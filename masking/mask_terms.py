#!/usr/bin/env python3
import argparse
import json
import logging
import os
import regex as re
import sys

from collections import defaultdict, namedtuple
from typing import List, Optional


def is_comment_or_empty(s: str) -> str:
    return s.startswith('#') or re.search(r'^\s*$', s)


def singlespace(s: str) -> str:
    if s is not None:
        s = re.sub(r' +', ' ', s.strip())
        #s = re.sub(r' +', ' ', s)
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
        
        for file in pattern_files:
            self.load_patterns(file, plabel_override)
        
        for file in dict_files:
            self.load_terms(file, dlabel_override)

        self.counts = defaultdict(int)
        self.counts_missed = defaultdict(int)
        self.counts_dupes = defaultdict(int)

        self.mask_matcher = re.compile(r'^__[A-Z][A-Z0-9_]*,\d+__$')
    
    def reset_counts(self):
        self.counts = defaultdict(int)
        self.counts_missed = defaultdict(int)

    def load_terms(self, file: str, label_override: Optional[str] = None):
        with open(file, encoding='UTF-8') as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                elements = line.rstrip().split('|||')
                if len(elements) < 3:
                    raise Exception('Invalid dictionary file: all lines must have a label')
                term = elements[0].strip()
                translation = elements[1].strip()
                if label_override:
                    label = label_override
                else:
                    label = elements[2].strip()
                    
                if term in self.terms:
                    self.counts_dupes[term] += term
                else:
                    self.terms[term] = (translation, label)

    def load_patterns(self, file: str, label_override: Optional[str] = None):
        with open(file, encoding='UTF-8') as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                elements = line.rstrip().split('|||')
                if len(elements) < 1:
                    raise Exception('Invalid pattern file: all lines must have a label')
                pattern = elements[0].strip()
                if label_override:
                    label = label_override
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
            return ' __{}_{}__ '.format(label, index)
    
    def unmask(self, output, masks):
        """
        Removes masks.

        """
        unmasked = output
        for mask in masks:
            print(mask)
            maskstr = mask["maskstr"]
            replacement = mask["replacement"]
            print("before:",unmasked)
            unmasked = unmasked.replace(maskstr," "+replacement+" ")
            print("after:",unmasked)
        
        return singlespace(unmasked)

    def mask(self, orig_source, orig_target: Optional[str] = None):
        masked_source, masked_target, term_masks = self.mask_by_term(orig_source, orig_target)
        masked_source, masked_target, pattern_masks = self.mask_by_pattern(masked_source, masked_target)
        term_masks.extend(pattern_masks)
        return singlespace(masked_source), singlespace(masked_target), term_masks
    
    def get_label_masks(self, label, source_pattern, translation, source, target: Optional[str] = None):
        masks = []
        source_matches = re.finditer(source_pattern, source)
        for source_match in source_matches:
            unmask_string = translation
            if translation is None:
                unmask_string = source_match.group()
            target_match = None
            if target is not None:
                target_match = re.search(re.escape(unmask_string), target)
            
            if target is None or target_match is not None:
                # don't apply index to masks until after applying patterns because digits
                # actually do, just use _ instead of ',' so it won't be a boundary. Problem solved!
                self.counts[label] += 1
                if self.add_index:
                    labelstr = self.get_mask_string(label, self.counts[label])
                else:
                    labelstr = self.get_mask_string(label)
                source = re.sub(source_pattern, labelstr, source, 1)
                if target is not None:
                    target = re.sub(re.escape(unmask_string), labelstr, target, 1)
                mask = { "maskstr":labelstr.strip(), "matched":source_match.group(), "replacement":unmask_string}
                masks.append(mask)
            else:
                self.counts_missed[label] += 1
        return source, target, masks
        
    def mask_by_term(self, orig_source, orig_target: Optional[str] = None):
        source_masks =[]
        source = orig_source
        target = orig_target
        for term in self.terms:
            translation, label = self.terms[term]
            pattern = r"\b"+re.escape(term)+r"\b"
            source, target, term_masks = self.get_label_masks(label, pattern, translation, source, target)
            source_masks.extend(term_masks)            
        return source, target, source_masks
    
    def mask_by_pattern(self, orig_source, orig_target: Optional[str] = None):
        source_masks = []
        source = orig_source
        target = orig_target
        for pattern, label in self.patterns:
            translation = None
            source, target, pattern_masks = self.get_label_masks(label, pattern, translation, source, target)
            source_masks.extend(pattern_masks)
        return source, target, source_masks

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
            masker.reset_counts()
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
