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

Breaking this apart, this chain takes raw text and turns it into a JSON object with the raw text in the `raw_text` field,
and also setting the `text` field (which always contains the output of the last operation):

```bash
cat raw_text.txt \
  | $SCRIPTS/preparation/wrap_in_json -r raw_text \
```

it then calls the Moses tokenizer, operating on the `text` field and writing to the `tok_text` field:

```bash
  | $SCRIPTS/preparation/wrap_in_json text tok_text moses_tokenizer \
```

You can find [moses_tokenizer here](https://github.com/mjpost/bin/blob/master/moses_tokenizer).
Next, we apply the subword operator, in this case, BPE:

```bash
  | $SCRIPTS/preparation/prepare.py --subword-type bpe --subword-model /path/to/subword/model \
```

Finally, we compute source factors.
This uses a number of fields and adds four source factors:

```
  | python3 -m source_factors.compute --json subword email number url
```

You can write your own by extending `compute.py` and `factors.py`.
