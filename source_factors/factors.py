# *-* encoding: utf-8 *-*

from abc import ABC, abstractmethod
from typing import Dict

class Factor(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def compute(self, segment: str):
        """
        Computes the factor on the tokens in the segment.
        """
        raise NotImplementedError()

    def compute_json(self,
                     jobj: Dict):
        """
        Extracts the required field from the JSON object and calls compute() with it.
        """
        raise NotImplementedError()


class SubwordFactor(Factor):
    def __init__(self):
        pass

    def compute_sp(self, sp_str: str) -> str:
        """
        iron cement is a ready for use paste which is laid as a fillet by putty knife or finger in the mould edges ( corners ) of the steel ingot mould .
        ▁iron ▁c ement ▁is ▁a ▁ready ▁for ▁use ▁past e ▁which ▁is ▁laid ▁as ▁a ▁fill et ▁by ▁put ty ▁kni fe ▁or ▁finger ▁in ▁the ▁mould ▁edge s ▁( ▁corner s ▁) ▁of ▁the ▁steel ▁in go t ▁mould ▁.

        The options are:
        O: a complete word
        B: beginning of a multi-token word
        I: interior of a multi-token word
        E: end of a multi-token word
        """

        def process_stack(stack):
            factors_ = []
            if len(stack) == 1:
                factors.append('O')
            elif len(stack) > 1:
                stack[0] = 'B'
                # all interior words are 'I'
                for i in range(1, len(stack) - 1):
                    stack[i] = 'I'
                stack[-1] = 'E'
                factors_ += stack
            return factors_

        factors = []
        tokens = sp_str.split()
        stack = [tokens.pop(0)]
        for i, token in enumerate(tokens):
            if token.startswith('▁'):
                factors += process_stack(stack)
                stack = []
            stack.append(token)

        factors += process_stack(stack)

        return ' '.join(factors)

    def compute_bpe(self, bpe_str: str) -> str:
        """
        Computes NER-style features for a BPE stream. e.g.,

        The boy ate the waff@@ le .
          O   O   O   O      B  E O

        The options are:
        O: a complete word
        B: beginning of a multi-token word
        I: interior of a multi-token word
        E: end of a multi-token word

        :param bpe_str: The BPE string.
        :return: A string of BPE factors.
        """
        factors = []
        was_in_bpe = False
        for i, token in enumerate(bpe_str.split()):
            now_in_bpe = token.endswith('@@')
            if was_in_bpe:
                if now_in_bpe:
                    factor = 'I'
                else:
                    factor = 'E'
            else:
                if now_in_bpe:
                    factor = 'B'
                else:
                    factor = 'O'

            was_in_bpe = now_in_bpe
            factors.append(factor)

        return ' '.join(factors)

    def compute(self, subword_str) -> str:
        """
        Computes features over a subword string.
        Automatically determines whether its SentencePiece or BPE.
        """

        return self.compute_sp(subword_str) if '▁' in subword_str else self.compute_bpe(subword_str)

    def compute_json(self, jobj):
        return self.compute(jobj['subword_text'])


class CaseFactor(Factor):
    def __init__(self):
        pass

    def case(self, token):
        if token.isupper():
            return 'UPPER'
        elif token.istitle():
            return 'Title'
        elif token.islower():
            return 'lower'
        else:
            return '-'

    def compute(self, segment: str) -> str:
        return ' '.join([self.case(token) for token in segment.split()])

    def compute_json(self, jobj: Dict) -> str:
        return self.compute(jobj['tok_text'])
        
