#!/usr/bin/env python3

"""
Takes a set of inputs and constraints as JSON objects, plus the system output, and
plots where the constraint appears in the output.
"""

import json
import sys

constraints = []
with open(sys.argv[1]) as system_in:
    for line in system_in:
        constraints.append(json.loads(line)['constraints'].replace('@@ ', ''))

sys_lines = []
with open(sys.argv[2]) as sys_in:
    sys_lines = sys_in.readlines()

ref_lines = []
with open(sys.argv[3]) as ref_in:
    ref_lines = ref_in.readlines()

for constraint, sys, ref in zip(constraints, sys_lines, ref_lines):
    print(constraint, sys, ref, sep='\n')
