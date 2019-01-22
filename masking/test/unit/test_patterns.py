# -*- coding: utf-8 -*-

import pytest
from mask_terms import TermMasker

TEST_PATTERNS_FILE = "/export/c11/shuoyangd/projects/whale19_masking/scripts/sockeye-scripts/masking/patterns.txt"
TEST_INPUT_FILE = "/export/c11/shuoyangd/projects/whale19_masking/scripts/sockeye-scripts/masking/test/test.txt"
TEST_OUTPUT_FILE = "/export/c11/shuoyangd/projects/whale19_masking/scripts/sockeye-scripts/masking/test/intended_test_output_annotated.txt"
ADD_INDEX = False
PLABEL = None
DLABEL = None

masker = TermMasker([TEST_PATTERNS_FILE], [], ADD_INDEX, PLABEL, DLABEL)

test_cases = []
for line, expected in zip(open(TEST_INPUT_FILE), open(TEST_OUTPUT_FILE)):
    line, expected = line.strip(), expected.strip()
    comment_pos = expected.find('#')
    if comment_pos != -1:
        expected = expected[:comment_pos]
    test_cases.append((line, expected))

@pytest.mark.parametrize("line, expected", test_cases)
def test_mask(line, expected, json=False):

    jobj = None
    if json:
        jobj = json.loads(line)
        line = jobj['text']
    else:
        line = line.rstrip('\n')

    if '\t' in line:
        orig_source, orig_target = line.split('\t', 1)
    else:
        orig_source = line
        orig_target = None

    masked_source, masked_target, masks = masker.mask(orig_source, orig_target)

    if orig_target is None:
        assert(masked_source == expected)
    else:
        masked = masked_source + "\t" + masked_target
        assert(masked == expected)

"""
@pytest.mark.parametrize("line, expected", test_cases)
def test_unmask(line, expected, json=False):

    jobj = None
    if json:
        jobj = json.loads(line)
        line = jobj['text']
    else:
        line = line.rstrip('\n')

    if not json:
        raise Exception('Unmasking requires json format')

    output = jobj['masked_output']
    masks = jobj['masks']
    unmasked = masker.unmask(output, masks)
    assert(unmasked == expected)
"""
