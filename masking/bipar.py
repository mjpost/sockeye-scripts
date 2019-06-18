#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2019 Shuoyang Ding <shuoyangd@gmail.com>
# Created on 2019-06-12
#
# Distributed under terms of the MIT license.

"""
Aligns unindexed masks.

Takes a one-line JSON object with the following fields:

- `subword_text`
- `attention`
- `translation`
- `masks`

It then uses the `attention` values to compute an alignment between `subword_text` and `translation`.
This alignment is in turn used to unmask the masked input.
The unmasked string is added to the JSON object as `unmasked_translation`.
"""

from munkres import Munkres, print_matrix
import json
import numpy
import sys

# this is a test
# lines = ["""{"masked_text": "Vendu au plus offrant après avoir passé __NUMBER__ mois sur le banc.", "masks": [{"maskstr": "__NUMBER__", "matched": "5", "replacement": "5"}], "raw_text": "Vendu au plus offrant après avoir passé 5 mois sur le banc.", "score": 0.510886013507843, "sentence_id": 16, "subword_method": "bpe", "subword_text": "V@@ endu au plus offrant après avoir passé __NUMBER__ mois sur le ban@@ c .", "text": "Lendu at the highest bidder after 5 months on the bench.", "tok_text": "Vendu au plus offrant après avoir passé __NUMBER__ mois sur le banc .", "translation": "L@@ endu at the highest bi@@ d@@ der after __NUMBER__ months on the b@@ ench .", "merged_text": "Lendu at the highest bidder after __NUMBER__ months on the bench .", "detok_translation": "Lendu at the highest bidder after __NUMBER__ months on the bench.", "unmasked_translation": "Lendu at the highest bidder after 5 months on the bench.", "attention": [[0.36, 0.87, 0.52, 0.65, 0.97, 0.75, 0.94, 0.92, 0.58, 0.25, 0.68, 0.02, 0.57, 0.72, 0.42, 0.54], [0.19, 0.66, 0.15, 0.04, 0.13, 0.84, 0.52, 0.32, 0.76, 0.46, 0.25, 0.94, 0.44, 0.18, 0.06, 0.86], [0.8, 0.44, 0.93, 0.27, 0.17, 0.73, 0.92, 0.18, 0.97, 0.06, 0.89, 0.47, 0.79, 0.02, 0.96, 0.45], [0.8, 0.44, 0.04, 0.16, 0.0, 0.03, 0.17, 0.49, 0.25, 0.97, 0.59, 0.68, 0.75, 0.15, 0.6, 0.84], [0.73, 0.12, 0.06, 0.67, 0.77, 0.49, 0.16, 0.29, 0.01, 0.36, 0.87, 0.6, 0.15, 0.4, 0.64, 0.85], [0.56, 0.03, 0.36, 0.71, 0.55, 0.53, 0.45, 0.82, 0.96, 0.09, 0.57, 0.06, 0.35, 0.68, 0.61, 0.4], [0.35, 1.0, 0.49, 0.91, 0.05, 0.16, 0.16, 0.94, 0.92, 0.83, 0.34, 0.02, 0.66, 0.04, 0.58, 0.75], [0.7, 0.27, 0.5, 0.72, 0.58, 0.93, 0.44, 0.29, 0.21, 0.44, 0.98, 0.11, 0.15, 0.47, 0.37, 0.27], [0.73, 0.21, 0.74, 0.07, 0.25, 0.93, 0.32, 0.38, 0.75, 0.61, 0.39, 0.45, 0.69, 0.75, 0.65, 0.11], [0.91, 0.16, 0.89, 0.59, 0.01, 0.86, 0.32, 0.6, 0.34, 0.64, 0.7, 0.47, 0.02, 0.36, 0.49, 0.48], [0.06, 0.56, 0.28, 0.85, 0.11, 0.46, 0.28, 0.75, 0.59, 0.74, 0.66, 0.63, 0.71, 0.89, 0.84, 0.92], [0.77, 0.21, 0.56, 0.52, 0.97, 0.08, 0.52, 0.01, 0.48, 0.44, 0.58, 0.0, 0.81, 0.9, 0.77, 0.04], [0.71, 0.46, 0.56, 0.26, 0.29, 0.34, 0.15, 0.34, 0.9, 0.72, 0.67, 0.3, 0.02, 0.13, 0.91, 0.99], [0.11, 0.91, 0.23, 0.15, 0.18, 0.95, 0.64, 0.52, 0.34, 0.66, 0.71, 0.09, 0.37, 0.08, 0.68, 0.17], [0.81, 0.41, 0.09, 0.16, 0.55, 0.48, 0.42, 0.06, 0.92, 0.74, 0.92, 0.28, 0.09, 0.19, 0.87, 0.72]]}
# """,
# """{"masked_text": "__CITY__ : Provoc, __PERSON__ se fait chahuter et insulter par les manifestants opposés à son concert Laisse béton.", "masks": [{"maskstr": "__PERSON__", "matched": "Bertrand Cantat", "replacement": "Bertrand Cantat"}, {"maskstr": "__CITY__", "matched": "Grenoble", "replacement": "Grenoble"}], "raw_text": "Grenoble: Provoc, Bertrand Cantat se fait chahuter et insulter par les manifestants opposés à son concert  Laisse béton.", "score": 0.5397155284881592, "sentence_id": 17, "subword_method": "bpe", "subword_text": "__CITY__ : Pro@@ vo@@ c , __PERSON__ se fait cha@@ hu@@ ter et insul@@ ter par les manifestants opposés à son concert L@@ aisse bét@@ on .", "text": "Grenoble : Provoc, Bertrand Cantat is heckling and insulting by demonstrators opposed to his concrete ballots.", "tok_text": "__CITY__ : Provoc , __PERSON__ se fait chahuter et insulter par les manifestants opposés à son concert Laisse béton .", "translation": "__CITY__ : Pro@@ vo@@ c , __PERSON__ is hec@@ k@@ ling and insul@@ ting by demonstrators opposed to his concrete bal@@ lots .", "merged_text": "__CITY__ : Provoc , __PERSON__ is heckling and insulting by demonstrators opposed to his concrete ballots .", "detok_translation": "__CITY__: Provoc, __PERSON__ is heckling and insulting by demonstrators opposed to his concrete ballots.", "unmasked_translation": "Grenoble : Provoc, Bertrand Cantat is heckling and insulting by demonstrators opposed to his concrete ballots.", "attention": [[0.69, 0.66, 0.53, 0.02, 0.22, 0.43, 0.03, 0.92, 0.87, 0.77, 0.54, 0.21, 0.36, 0.83, 0.24, 0.37, 0.47, 0.03, 0.69, 0.46, 0.27, 0.49, 0.27], [0.43, 0.85, 0.68, 0.81, 0.53, 0.22, 0.81, 0.24, 0.12, 0.72, 0.95, 0.95, 0.71, 0.25, 0.65, 0.16, 0.7, 0.58, 0.48, 0.46, 0.28, 0.55, 0.79], [0.36, 0.66, 0.45, 0.22, 0.01, 0.46, 0.49, 0.77, 0.44, 0.75, 0.75, 0.07, 0.8, 0.48, 0.93, 0.34, 0.24, 0.69, 0.77, 0.09, 0.16, 0.08, 0.34], [0.9, 0.05, 0.92, 0.58, 0.77, 0.47, 0.1, 0.03, 0.02, 0.62, 0.19, 0.61, 0.51, 0.31, 0.99, 0.17, 0.61, 0.58, 0.78, 0.6, 0.27, 0.81, 0.81], [0.13, 0.55, 0.52, 0.29, 0.65, 0.85, 0.99, 0.05, 0.55, 0.78, 0.01, 0.66, 0.67, 0.31, 0.29, 0.99, 0.75, 0.55, 0.59, 0.14, 0.73, 0.56, 0.98], [0.69, 0.59, 0.47, 0.87, 0.44, 0.52, 0.39, 0.38, 0.13, 0.65, 0.4, 0.11, 0.48, 0.73, 0.41, 0.94, 0.62, 0.04, 0.39, 0.29, 0.5, 0.79, 0.42], [0.53, 0.41, 0.18, 0.55, 0.82, 0.71, 0.43, 0.14, 0.64, 0.86, 0.52, 0.46, 0.81, 0.13, 0.38, 0.27, 0.09, 0.56, 0.57, 0.72, 0.45, 0.79, 0.18], [0.73, 0.09, 0.33, 0.79, 0.33, 0.34, 0.0, 0.77, 0.49, 0.04, 0.07, 0.13, 0.72, 0.67, 0.91, 0.44, 0.9, 0.17, 0.5, 0.2, 0.12, 0.78, 0.17], [0.12, 0.05, 0.34, 0.99, 0.09, 0.26, 0.18, 0.26, 0.57, 0.34, 0.02, 0.64, 0.73, 0.21, 0.51, 0.87, 0.22, 0.5, 0.66, 0.02, 0.78, 0.02, 0.64], [0.14, 0.09, 0.83, 0.31, 0.12, 0.4, 0.38, 0.09, 0.94, 0.05, 0.47, 0.18, 0.21, 0.39, 0.05, 0.66, 0.84, 0.34, 0.71, 0.83, 0.64, 0.25, 0.92], [0.34, 0.38, 0.24, 0.73, 0.39, 0.75, 0.98, 0.39, 0.96, 0.91, 0.45, 0.8, 0.3, 0.66, 0.06, 0.8, 0.52, 0.71, 0.32, 0.75, 0.3, 0.9, 0.42], [0.88, 0.21, 0.72, 0.81, 0.06, 0.83, 0.82, 0.69, 0.26, 0.88, 0.53, 0.68, 0.26, 0.51, 0.55, 0.32, 0.7, 0.66, 0.76, 0.97, 0.21, 0.02, 0.85], [0.9, 0.59, 0.02, 0.24, 0.56, 0.43, 0.35, 0.11, 0.85, 0.86, 0.38, 0.29, 0.98, 0.96, 0.92, 0.91, 0.03, 0.37, 0.03, 0.62, 0.34, 0.19, 0.08], [0.23, 0.84, 0.57, 0.75, 0.75, 0.52, 0.5, 0.31, 0.02, 0.68, 0.38, 0.48, 0.47, 0.59, 0.74, 0.58, 0.57, 0.89, 0.74, 0.69, 0.97, 0.13, 0.88], [0.1, 0.4, 0.91, 0.4, 0.91, 0.98, 0.42, 0.6, 0.81, 0.24, 0.03, 0.44, 0.92, 0.55, 0.24, 0.0, 0.04, 0.65, 0.22, 0.63, 0.26, 0.3, 0.03], [0.94, 0.78, 0.17, 0.77, 0.07, 0.95, 0.5, 0.23, 0.54, 0.27, 0.88, 0.44, 0.64, 0.35, 0.13, 0.78, 0.75, 0.68, 0.97, 0.82, 0.49, 0.79, 0.17], [0.34, 0.51, 0.76, 0.14, 0.68, 0.38, 0.65, 0.7, 0.61, 0.96, 0.94, 0.19, 0.32, 0.85, 0.82, 0.62, 0.12, 0.11, 0.36, 0.44, 0.05, 0.0, 0.34], [0.39, 0.38, 0.42, 0.06, 0.55, 0.73, 0.89, 0.6, 0.45, 0.74, 0.25, 0.41, 0.28, 0.58, 0.68, 0.39, 0.8, 0.86, 0.59, 0.25, 0.19, 0.49, 0.63], [0.33, 0.4, 0.13, 0.05, 0.95, 0.09, 0.88, 0.02, 0.72, 0.41, 0.09, 0.82, 0.73, 0.79, 0.54, 0.45, 0.04, 0.81, 0.38, 0.71, 0.13, 0.98, 0.87], [0.71, 0.81, 0.46, 0.79, 0.04, 0.49, 0.72, 0.18, 0.04, 0.64, 0.46, 0.99, 0.84, 0.14, 0.25, 0.73, 0.15, 0.77, 0.93, 0.2, 0.43, 0.68, 0.2], [0.21, 0.7, 0.41, 0.57, 0.75, 0.92, 0.87, 0.1, 0.77, 0.33, 0.09, 0.86, 0.67, 0.29, 0.38, 0.32, 0.38, 0.91, 0.19, 0.47, 0.32, 0.89, 0.0], [0.69, 0.08, 0.89, 0.56, 0.47, 0.39, 0.88, 0.67, 0.84, 0.81, 0.81, 0.27, 0.19, 0.68, 0.4, 0.37, 0.29, 0.3, 0.21, 0.92, 0.3, 0.55, 0.86], [0.91, 0.23, 0.26, 0.82, 0.84, 0.46, 0.14, 0.42, 0.5, 0.43, 0.86, 0.97, 0.24, 0.71, 0.92, 0.35, 0.31, 0.65, 0.19, 0.47, 0.76, 0.6, 0.22], [0.25, 0.3, 0.06, 0.14, 0.37, 0.76, 0.71, 0.98, 0.03, 0.17, 0.46, 0.02, 0.92, 0.29, 0.11, 0.2, 0.94, 0.01, 0.4, 0.02, 0.51, 0.61, 0.33], [0.33, 0.22, 0.75, 0.94, 0.27, 0.48, 0.82, 0.91, 0.54, 0.57, 0.48, 0.5, 0.13, 0.09, 0.33, 0.15, 0.18, 0.98, 0.78, 0.63, 0.17, 0.13, 0.06], [0.23, 0.87, 0.44, 0.39, 0.98, 0.81, 0.52, 0.16, 0.7, 0.82, 0.38, 0.02, 0.54, 0.48, 0.9, 0.27, 0.52, 0.28, 0.54, 0.82, 0.35, 0.71, 0.09], [0.64, 0.44, 0.03, 0.67, 0.56, 0.27, 0.88, 0.8, 0.7, 0.35, 0.56, 0.93, 0.8, 0.62, 0.57, 0.16, 0.99, 0.14, 0.23, 0.93, 0.04, 0.22, 0.65]]}
# """]

def is_mask(tok):
    if tok.startswith("__") and tok.endswith("__") and tok[2:-2].isupper():
        return True
    else:
        return False


m = Munkres()
for lineno, line in enumerate(sys.stdin, 1):
# for line in lines:
    obj = json.loads(line)
    
    target_masked_toks = obj["translation"].strip().split()  # attention is on bpe-level, so cannot use merged text
    target_mask_index_str = { j: target_masked_toks[j] for j in range(len(target_masked_toks)) if is_mask(target_masked_toks[j]) }
    target_mask_str_index = {}
    for key, value in target_mask_index_str.items():
        target_mask_str_index.setdefault(value, list()).append(key)
    source_toks = obj["subword_text"].strip().split()
    attention = -numpy.array(obj["attention"]).transpose()
    masks = obj["masks"]

    # for each identical mask
    for key in target_mask_str_index.keys():
        source_mask_indexes = numpy.array(sorted([ i for i in range(len(source_toks)) if source_toks[i] == key ]))
        target_mask_indexes = numpy.array(target_mask_str_index[key])
        effective_attention = attention[source_mask_indexes, :][:, target_mask_indexes]
        # Munkres has shape requirements, so fool it if needed
        transpose = effective_attention.shape[0] > effective_attention.shape[1]
        if transpose:
            effective_attention = effective_attention.transpose()
        # compute bipartite matching
        matches = m.compute(effective_attention)
        if transpose:
            matches = [ (j, i) for i, j in matches ]

        source_mask_replacements = [ mask["replacement"] for mask in masks if mask["maskstr"] == key ]
        for i, j in matches:
            target_masked_toks[target_mask_indexes[j]] = source_mask_replacements[i]

    obj["unmasked_translation"] = " ".join(target_masked_toks)
    obj['text'] = obj['unmasked_translation']
    print(json.dumps(obj, ensure_ascii=False))
    
