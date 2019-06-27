#!/usr/bin/env python3
import argparse
import json
import logging
import os
import random
import regex as re
import sys

from collections import defaultdict, namedtuple
from typing import List, Optional, Tuple, Dict
from operator import itemgetter


def is_comment_or_empty(s: str) -> str:
    return s.startswith('#') or re.search(r'^\s*$', s)


def singlespace(s: str) -> str:
    if s is not None:
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

        self.default_label = "TERM"

        self.add_index = add_index

        for file in pattern_files:
            self.load_patterns(file, plabel_override)

        for file in dict_files:
            self.load_dictionary(file, dlabel_override)

        self.counts = defaultdict(int)
        self.counts_missed = defaultdict(int)

    def reset_counts(self):
        self.counts = defaultdict(int)
        self.counts_missed = defaultdict(int)

    def load_dictionary(self, file: str, label_override: Optional[str] = None):
        """
        Loads dictionary terms from a file.
        Dictionaries are just like pattern matches except (a) they do not use regular expressions
        and (b) the target side can be different from the source.

        Their format is

        source TAB target TAB label
        """

        with open(file, encoding='UTF-8') as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                elements = line.rstrip().split('\t')
                label = self.default_label
                if len(elements) == 2:
                    term, replacement = elements
                elif len(elements) == 3:
                    term, replacement, label = elements
                else:
                    raise Exception('Dictionaries require two or three fields')

                if label_override:
                    label = label_override

                # TODO: Deal with multiple translations
                #   We have no way to tell which one to pick now, so just go with the first
                if term not in self.terms:
                    self.terms[term] = (replacement, label)

    def load_patterns(self,
                      file: str,
                      label_override: Optional[str] = None):
        """
        Loads patterns from a file.
        Patterns are of the form

            PATTERN ||| MASK

        where PATTERN is a regular expression (matching anywhere in the string) and MASK
        the mask to replace it with.
        If `label_override` is defined, it will be used as the mask always.
        """
        with open(file, encoding='UTF-8') as infh:
            for line in infh:
                if is_comment_or_empty(line):
                    continue

                elements = line.rstrip().split('|||')
                if len(elements) < 1:
                    raise Exception('Invalid pattern file: all lines must have a label')
                pattern = elements[0].strip()
                label = label_override if label_override else elements[1].strip()

                # Boundary checking also needs to be handled in the patterns themselves
                # because the behavior is different with word/non-word characters
                # on the edges!
                self.patterns.append((pattern, label))

    def get_mask_string(self,
                        label: str,
                        index: Optional[int] = None):
        """
        Computes the mask for strings, adding the index if required.
        """
        if self.add_index:
            return ' __{}_{}__ '.format(label, index)
        else:
            return ' __{}__ '.format(label)

    def unmask(self, output, masks):
        """
        Removes masks.

        """
        unmasked = ' {} '.format(output)
        for mask in masks:
            maskstr = mask["maskstr"]
            replacement = mask["replacement"]
            unmasked = unmasked.replace(maskstr, " " + replacement + " ")

        return singlespace(unmasked)

    def mask(self, orig_source, orig_target: Optional[str] = None, prob = 1.0):
        masked_source, masked_target, term_masks = self.mask_by_term(orig_source, orig_target, prob)
        masked_source, masked_target, pattern_masks = self.mask_by_pattern(masked_source, masked_target, prob)
        term_masks.extend(pattern_masks)
        return singlespace(masked_source), singlespace(masked_target), term_masks

    def get_label_masks(self,
                        label,
                        source_pattern,
                        translation,
                        source,
                        target: Optional[str] = None,
                        prob: float = 1.0) -> Tuple[str, str, Dict]:
        """
        Search for `source_pattern` in `source`.
        If `target` is None, replace the matched text with `label`.
        If `target` is not None, replace the matched text with `label` only if `translation` can be found in `target`.
        If `translation` is None, the matched text is used to match against `target` instead.
        """
        masks = []
        source_mods = []
        target_mods = []
        for source_match in re.finditer(source_pattern, source):
            matched_text = source_match.group()
            source_match_position = source_match.start()
            replacement_text = translation if translation is not None else matched_text
            loc_in_target = -1 if target is None else target.find(replacement_text)

            if target is None or loc_in_target != -1:
                self.counts[label] += 1
                labelstr = self.get_mask_string(label, self.counts[label])
                mask = { "maskstr" : labelstr.strip(), "matched" : matched_text, "replacement" : replacement_text }

                if target is not None:
                    if random.random() < prob:
                        source_mods.append((source_match_position, len(matched_text), labelstr))
                        target_mods.append((loc_in_target, len(replacement_text), labelstr))
                        masks.append(mask)
                else:
                    # Always apply at test time
                    source_mods.append((source_match_position, len(matched_text), labelstr))
                    masks.append(mask)
            else:
                self.counts_missed[label] += 1

        # sort the target mods!
        target_mods = sorted(target_mods, key=itemgetter(0))

        def apply_mods(text, mod_list):
            if mod_list:
                offset = 0
                for i, matched_len, mask in mod_list:
                    i += offset
                    text = text[0:i] + mask + text[i + matched_len:]
                    offset += len(mask) - matched_len
            return text

        source = apply_mods(source, source_mods)
        target = apply_mods(target, target_mods)

        return source, target, masks

    def mask_by_term(self,
                     orig_source,
                     orig_target: Optional[str] = None,
                     prob = 1.0):
        """
        Masks using dictionary entries.
        """

        source_masks = []
        source = orig_source
        target = orig_target
        for term, (translation, label) in self.terms.items():
            if term in source:
                pattern = r'\b{}\b'.format(re.escape(term))
                source, target, term_masks = self.get_label_masks(label, pattern, translation, source, target, prob)
                source_masks.extend(term_masks)

        return source, target, source_masks

    def mask_by_pattern(self, orig_source, orig_target: Optional[str] = None, prob = 1.0):
        """
        Masks using regex patterns.
        """
        source_masks = []
        source = orig_source
        target = orig_target
        for pattern, label in self.patterns:
            translation = None
            source, target, pattern_masks = self.get_label_masks(label, pattern, translation, source, target, prob)
            source_masks.extend(pattern_masks)
        return source, target, source_masks

def main(args):

    if args.constrain and not args.json:
        print("Can't add constraints with --json", file=sys.stderr)
        sys.exit(1)

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

            # get the output from the last step, plus the masks, and unmask
            output = jobj['text']
            masks = jobj['masks']
            unmasked = masker.unmask(output, masks)
            jobj['unmasked_translation'] = jobj['text'] = unmasked
            print(json.dumps(jobj), flush=True)

        else:
            masker.reset_counts()
            if '\t' in line:
                orig_source, orig_target = line.split('\t', 1)
            else:
                orig_source = line
                orig_target = None

            masked_source, masked_target, masks = masker.mask(orig_source, orig_target, args.prob)

            if orig_target is None:
                if args.json:
                    jobj['masked_text'] = jobj['text'] = masked_source
                    jobj['masks'] = masks

                    if args.constrain:
                        jobj['constraints'] = [mask['maskstr'] for mask in masks]

                    print(json.dumps(jobj, ensure_ascii=False), flush=True)
                else:
                    print(masked_source, flush=True)
            else:
                print(masked_source, masked_target, sep='\t', flush=True)

            if args.dump_masks:
                if len(masks) > 0:
                    print(json.dumps({'masks': masks}, ensure_ascii=False), flush=True, file=args.dump_masks)
                else:
                    print(file=args.dump_masks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pattern-files', '-p', nargs='+', type=str,
                        default=[],
                        help='List of files with patterns')
    parser.add_argument('--dict-files', '-d', nargs='+', type=str,
                        default=[],
                        help='List of files with terminology')
    parser.add_argument('--pattern-label', '-l', type=str,
                        default=None,
                        help='Override labels in pattern files with this label')
    parser.add_argument('--dict-label', '-t', type=str,
                        default=None,
                        help='Override labels in dictionary files with this label')
    parser.add_argument('--json', '-j', action='store_true',
                        help='JSON input and output')
    parser.add_argument('--add-index', '-i', action='store_true',
                        help='Add an index to each mask')
    parser.add_argument('--unmask', '-u', action='store_true',
                        help='Perform unmasking')
    parser.add_argument('--constrain', '-c', action='store_true',
                        help='Add masks as positive constraints')
    parser.add_argument('--dump-masks',
                        type=argparse.FileType('wt'),
                        default=None,
                        help='File to write mask JSON object to.')
    parser.add_argument('--prob', type=float, default=1.0,
                        help='Mask with specified probability. Default: %(default)s.')
    parser.set_defaults(func=lambda _: parser.print_help())
    args = parser.parse_args()

    main(args)
