# -*- coding: utf-8 -*-

import pytest
from mask_terms import TermMasker
import json

TEST_PATTERNS_FILE = "patterns.txt"
PATTERN_TEST_INPUT_FILE = "test/data/pattern_test.txt"
PATTERN_TEST_OUTPUT_FILE = "test/data/intended_pattern_test_output_annotated.txt"
DICT_TEST_DICT_FILE = "test/data/test_dict.txt"
DICT_TEST_INPUT_FILE = "test/data/dict_test.txt"
DICT_TEST_OUTPUT_FILE = "test/data/intended_dict_test_output_annotated.txt"

test_cases = []
for line, expected in zip(open(PATTERN_TEST_INPUT_FILE), open(PATTERN_TEST_OUTPUT_FILE)):
    line, expected = line.strip(), expected.strip()
    comment_pos = expected.find('#')
    if comment_pos != -1:
        expected = expected[:comment_pos].strip()
    test_cases.append((line, expected))

@pytest.mark.parametrize("line, expected", test_cases)
def test_pattern_mask(line, expected):
    masker = TermMasker([TEST_PATTERNS_FILE], [])
    orig_source = line.rstrip('\n')
    masked_source, masked_target, masks = masker.mask(orig_source)
    assert(masked_source == expected)

term_test_cases = []
for line, expected in zip(open(DICT_TEST_INPUT_FILE), open(DICT_TEST_OUTPUT_FILE)):
    line, expected = line.strip(), expected.strip()
    comment_pos = expected.find('#')
    if comment_pos != -1:
        expected = expected[:comment_pos].strip()
    term_test_cases.append((line, expected))

@pytest.mark.parametrize("line, expected", term_test_cases)
def test_term_mask(line, expected):
    masker = TermMasker([], [DICT_TEST_DICT_FILE])
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
