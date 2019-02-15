# *-* coding: utf-8 *-*

from abc import ABC
import re

class Subwordenizer(ABC):
    """
    Generic class for providing subword segmentation.
    This base class does nothing.
    """
    def __init__(self):
        pass

    def segment(self, line: str) -> str:
        return line

    def merge(self, line: str) -> str:
        return line


class BPE(Subwordenizer):
    """
    Implements BPE.
    """
    def __init__(self, model_path=None):
        from subword_nmt import apply_bpe
        self.unsegment_re = re.compile(r'@@( |$)')

        self.model = None
        if model_path is not None:
            self.model = apply_bpe.BPE(open(model_path))

    def segment(self, sentence) -> str:
        """Segments a string."""
        if self.model is None:
            raise Exception('No model loaded!')
        return self.model.segment(sentence)
        
    def merge(self, sentence) -> str:
        """Unsegments a string."""
        return self.unsegment_re.sub('', sentence)


class SentencePiece(Subwordenizer):
    """
    Implements SentencePiece.
    https://github.com/google/sentencepiece/blob/master/python/README.md
    """
    def __init__(self, model_path, alpha: float = 0.5):
        import sentencepiece as spm
        self.model = spm.SentencePieceProcessor()
        self.model.Load(model_path)
        self.alpha = alpha
        self.sample = True

    def segment(self, sentence) -> str:
        if self.sample:
            return ' '.join(self.model.SampleEncodeAsPieces(sentence, nbest_size=1, alpha=self.alpha))
        else:
            return ' '.join(self.model.EncodeAsPieces(sentence))

    def merge(self, sentence: str) -> str:
        return self.model.DecodePieces(sentence.split())
        

def get_subwordenizer(method, model_path):
    if method == 'bpe':
        return BPE(model_path)
    elif method == 'sentencepiece':
        return SentencePiece(model_path)
    else:
        return Subwordenizer()

