#!/usr/bin/env python3
"""
Extracts a JSON field from a JSON input object.

Author: Matt Post
"""

import json
import sys
import argparse

def main(args):

    for lineno, line in enumerate(sys.stdin, 1):
        jobj = json.loads(line)
        print(jobj[args.field], flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JSON wrapper')
    parser.add_argument('--field', '-f', type=str, default='text', help='The JSON input field to extract.')
    args = parser.parse_args()

    main(args)
