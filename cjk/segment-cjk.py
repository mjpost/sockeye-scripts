#!/usr/bin/env python3

"""
Character-based segmentation of Chinese, without any segmentation of non-Han characters.
If `--json` is passed, it will read the input line as a JSON object and tokenize the 'text'
field, updating that field and also adding a 'tok_text' field.
"""

import jieba
import json
import regex
import sys

def segment_char(line):
    # Chinese
    line = regex.sub(r'(\p{Han})', r' \1 ', line)
    # Korean
    line = regex.sub(r'(\p{Hangul})', r' \1 ', line)
    # Japenese
    line = regex.sub(r'(\p{Hiragana})', r' \1 ', line)
    line = regex.sub(r'(\p{Katakana})', r' \1 ', line)
    return line


def segment_jieba(text):
    return " ".join(jieba.cut(text))


def main(args):
    if args.method == "jieba":
        jieba.enable_parallel(4)

    for line in sys.stdin:
        jobj = None
        if args.json:
            jobj = json.loads(line)
            line = jobj['text']
        line = line.rstrip()

        if args.method == "char":
            line = segment_char(line)
        elif args.method == "jieba":
            line = segment_jieba(line)

        line = line.replace('  ', ' ').strip()
        if args.json:
            jobj['text'] = jobj['tok_text'] = line
            print(json.dumps(jobj, ensure_ascii=False), flush=True)
        else:
            print(line, flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Chinese character-based segmenter.")
    parser.add_argument("--method", "-m", choices=["char", "jieba"], default="char")
    parser.add_argument('--json', '-j', action='store_true', help="Read and write JSON.")
    args = parser.parse_args()

    main(args)
