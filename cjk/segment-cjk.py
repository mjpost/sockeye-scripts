#!/usr/bin/env python3

"""
Character-based segmentation of Chinese, without any segmentation of non-Han characters.
If `--json` is passed, it will read the input line as a JSON object and tokenize the 'text'
field, updating that field and also adding a 'tok_text' field.
"""

import argparse
import json
import regex
import sys

parser = argparse.ArgumentParser("Chinese character-based segmenter.")
parser.add_argument('--json', '-j', action='store_true', help="Read and write JSON.")
args = parser.parse_args()

for line in sys.stdin:
    jobj = None
    if args.json:
        jobj = json.loads(line)
        line = jobj['text']
    line = line.rstrip()

    # Chinese
    line = regex.sub(r'(\p{Han})', r' \1 ', line)
    # Korean
    line = regex.sub(r'(\p{Hangul})', r' \1 ', line)
    # Japenese
    line = regex.sub(r'(\p{Hiragana})', r' \1 ', line)
    line = regex.sub(r'(\p{Katakana})', r' \1 ', line)

    line = line.replace('  ', ' ').strip()
    if args.json:
        jobj['text'] = jobj['tok_text'] = line
        print(json.dumps(jobj, ensure_ascii=False), flush=True)
    else:
        print(line, flush=True)
