#!/usr/bin/env python3

"""
Takes a source, masked source, and target, and a fast_align model.
It runs fast_align to recover the alignments
"""

import argparse

def parse_alignments(align):
    t2s = {}
    for x in align.split(' '):
        s, t = x.split('-')
        t2s[int(t)] = int(s)
    return t2s


def ismask(word):
    return word.startswith('__')


def replace_masks(source, maskedsource, target, alignments, output):
    with open(source) as fsrc, open(maskedsource) as fmsrc, open(target) as ftgt, open(alignments) as falign, open(output, 'w') as fout:
        for src, msrc, tgt, align in zip(fsrc, fmsrc, ftgt, falign):
            src = src.strip().split(' ')
            msrc = msrc.strip().split(' ')
            tgt = tgt.strip().split(' ')

            align = align.strip()
            if align == '':
                print('empty align: ', src, tgt)
                print(tgt, file=fout)
                continue

            align = parse_alignments(align.strip())
            masked2orig = align_masked(src, msrc)

            try:
                output = tgt
                for t in align:
                    if ismask(tgt[t]):
                        output[t] = src[masked2orig[align[t]]]
            except:
                print(src)
                print(msrc)
                print(align)
                print(masked2orig)

            print(' '.join(output), file=fout)


def align_masked(source, masked_source):
    '''Masking may have added extra words. This function creates a map of indices from the masked source to the original source'''
    ms_idx = 0
    masked2orig = {}
    for src_idx in range(len(source)):
        if ms_idx >= len(masked_source):
            break
        masked2orig[ms_idx] = src_idx
        if ismask(masked_source[ms_idx]):
            while src_idx < len(source) - 1 and ms_idx < len(masked_source) - 1 and source[src_idx + 1] != masked_source[ms_idx + 1]:
                ms_idx += 1
                masked2orig[ms_idx] = src_idx
        ms_idx += 1
    while ms_idx < len(masked_source):
        masked2orig[ms_idx] = len(source) - 1
        ms_idx += 1
    return masked2orig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s')
    parser.add_argument('--maskedsource', '-ms')
    parser.add_argument('--target', '-mt', help='masked output from MT system')
    parser.add_argument('--alignments', '-a', help='alignments from fast_align')
    parser.add_argument('--output', '-o')
    args = parser.parse_args()

    replace_masks(args.source, args.maskedsource, args.target, args.alignments, args.output)

if __name__ == '__main__':
    # print(align_masked("a 1-2 b c".split(), "a __NUMBER__ - __NUMBER__ b c".split()))
    main()
