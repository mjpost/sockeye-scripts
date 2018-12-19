#!/usr/bin/env python3

import langid
import sys

_, src, trg = sys.argv

skipped_source = skipped_target = 0
for i, line in enumerate(sys.stdin, 1):
    src_line, trg_line = line.rstrip().split('\t')
    if langid.classify(src_line)[0] != src:
        skipped_source += 1
        continue
    elif langid.classify(trg_line)[0] != trg:
        skipped_target += 1
        continue
    print(src_line, trg_line, sep='\t')

print('Processed {} lines, skipping {} (source) and {} (target)'.format(i, skipped_source, skipped_target), file=sys.stderr)
