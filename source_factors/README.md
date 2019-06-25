# Source factors

This code adds source factors to tokenized word streams, and also allows you to broadcast those 
factors accross an associated subword stream computed from the tokenized stream.

Example usage:

```bash
SCRIPTS=/path/to/sockeye-scripts
export PYTHONPATH+=:$SCRIPTS
cat raw_text.txt \
  | $SCRIPTS/preparation/wrap_in_json -r raw_text \
  | $SCRIPTS/preparation/wrap_in_json text tok_text moses_tokenizer \
  | $SCRIPTS/preparation/prepare.py --subword-type bpe --subword-model /path/to/subword/model \
  | python3 -m source_factors.compute --json subword email number url
```
