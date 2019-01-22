# -*- coding: utf-8 -*-

import pytest
from mask_terms import TermMasker
import json

TEST_PATTERNS_FILE = "patterns.txt"
TEST_INPUT_FILE = "test/data/pattern_test.txt"
TEST_OUTPUT_FILE = "test/data/intended_test_output_annotated.txt"
TEST_DICT_FILE = "test/data/test_dict.txt"
TERM_INPUT_FILE = "test/data/dict_test.txt"
TERM_OUTPUT_FILE = "test/data/intended_dict_output_annotated.txt"


test_cases = []
for line, expected in zip(open(TEST_INPUT_FILE), open(TEST_OUTPUT_FILE)):
    line, expected = line.strip(), expected.strip()
    comment_pos = expected.find('#')
    if comment_pos != -1:
        expected = expected[:comment_pos]
    test_cases.append((line, expected))

@pytest.mark.parametrize("line, expected", test_cases)
def test_pattern_mask(line, expected):
    masker = TermMasker([TEST_PATTERNS_FILE], [])
    orig_source = line.rstrip('\n')
    masked_source, masked_target, masks = masker.mask(orig_source)
    assert(masked_source == expected)

term_test_cases = []
for line, expected in zip(open(TERM_INPUT_FILE), open(TERM_OUTPUT_FILE)):
    line, expected = line.strip(), expected.strip()
    comment_pos = expected.find('#')
    if comment_pos != -1:
        expected = expected[:comment_pos]
    term_test_cases.append((line, expected))

@pytest.mark.parametrize("line, expected", term_test_cases)
def test_term_mask(line, expected):
    masker = TermMasker([], [TEST_DICT_FILE])
    orig_source = line.rstrip('\n')
    masked_source, masked_target, masks = masker.mask(orig_source)
    assert(masked_source == expected)

json_test_cases = [("patterns.txt", "test/data/test_dict.txt", "test/data/test.json"),
              ("patterns.txt", "test/data/test_dict.txt", "test/data/test_cyrillic.json"),
              ("patterns.txt", "test/data/test_dict.txt", "test/data/test_multiword.json")
        ]
@pytest.mark.parametrize("pattern_file, dict_file, json_file", json_test_cases)
def test_json(pattern_file, dict_file, json_file):
    masker = TermMasker([pattern_file], [dict_file], add_index=True)
    with open (json_file) as jsonfile:
        jobj = json.load(jsonfile)
        orig_source = jobj['text']
        masked_source, masked_target, masks = masker.mask(orig_source)
        
        assert masked_source == jobj["expected_masked"]
        
        output = masked_source
        unmasked = masker.unmask(output, masks)
        
        assert unmasked == jobj["expected_unmasked"]



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
