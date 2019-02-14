#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Apply the specified pre-processing.
Each step of preprocessing (a) is recorded in its own field (e.g., "recased_text") and (b) overwrites the "text" field.
In this way, (a) each stage's output is recorded and (b) subsequent steps can always access the output of the immediately
preceding step without having to reason about what the previous step was.
"""

import json
import os
import sys
import argparse

import subword

def main(args):
    # sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    # sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', 0)

    subwordenizer = subword.get_subwordenizer(args.subword_type, args.subword_model)

    for lineno, line in enumerate(sys.stdin, 1):
        try:
            jobj = json.loads(line)
        except json.decoder.JSONDecodeError as e:
            print('Failed to parse JSON object from line {}: {}'.format(lineno, line.rstrip()))
            sys.exit(1)

        jobj['text'] = jobj[args.input_field]

        if args.casing.startswith('lower'):
            jobj['recased_text'] = jobj['text'] = jobj['text'].lower()
        elif args.casing == 'true':
            raise Exception('Truecasing not supported')

        if args.subword_type != 'none':
            if args.undo:
                jobj['merged_text'] = jobj['text'] = subwordenizer.merge(jobj['text'])
            else:
                jobj['subword_text'] = jobj['text'] = subwordenizer.segment(jobj['text'])
                jobj['subword_method'] = args.subword_type

        print(json.dumps(jobj, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Take in raw text, apply all preprocessing.')
    parser.add_argument('--subword-type', choices=['none', 'bpe', 'sentencepiece'], default='none', help='Subword method to apply. Default: %(default)s.')
    parser.add_argument('--subword-model', type=str, default=None, help='Location of subword model.')
    parser.add_argument('--casing', choices=['original', 'lower', 'lower_source', 'true'], default='original', help='Recasing to apply. Default: %(default)s.')
    parser.add_argument('--undo', '-u', action='store_true', help='Undo (i.e., apply post-processing).')
    parser.add_argument('--input-field', '-f', type=str, default='text', help='The JSON input field to begin work on.')

    # parser.add_argument('--mask', type=argparse.FileType('r'), help='Apply term masking with patterns from the specified file.')
    # parser.add_argument('--source-factors', type=str, nargs='+', default=None, help='Source factors to apply.')

    args = parser.parse_args()
    main(args)

