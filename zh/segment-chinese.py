#!/usr/bin/env python3

import regex
import sys

for line in sys.stdin:
    line = line.rstrip()
    line = regex.sub(r'(\p{Han})', r' \1 ', line)
    line = line.replace('  ', ' ').strip()
    print(line)
