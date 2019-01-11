#!/usr/bin/env python3

import argparse
import langid
import sys

def main(args):
    skipped_source = skipped_target = 0
    for i, line in enumerate(sys.stdin, 1):
        fields = line.rstrip().split('\t')
        src_line = fields[args.source_field]
        trg_line = fields[args.target_field]
        if langid.classify(src_line)[0] != args.source_lang:
            skipped_source += 1
            continue
        elif langid.classify(trg_line)[0] != args.target_lang:
            skipped_target += 1
            continue
        print(line.rstrip())

    print('Skipped {} / {} lines (source {} and target {})'.format(skipped_source + skipped_target, i,
                                                                   skipped_source, skipped_target), 
          file=sys.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_lang')
    parser.add_argument('target_lang')
    parser.add_argument('--source-field', '-sf', type=int, default=0)
    parser.add_argument('--target-field', '-tf', type=int, default=1)
    args = parser.parse_args()
    main(args)
