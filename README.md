Various scripts and utilities for working with sockeye.

- `prepare/`: A general purpose data preparation pipeline that can apply tokenization, masking, subword splitting, and source factors.
- `masking/`: code to mask out words at training and inference time.
- `source_factors/`: scripts for computing and applying source factors.
- `zh/`: for Chinese.
- `filtering/`: Implements [dual cross-entropy filtering](http://aclweb.org/anthology/W18-6478) of bitext.

## Model packaging

An important contribution of these scripts that requires further description is model packaging.
The idea of a model package is to tie together all the pre- and post-processing used in building a model.
The model can then be used as a black box, consuming raw (untokenized) input text and return raw (detokenized) output text.
This is important for a number of reasons:

- Preprocessing (including tokenization, subword splitting, normalization, masking and any number of other tools) are *model-specific decisions* that should not be exposed to the outside world
- In research pipelines, it can be difficult to remember which set of preprocessing scripts apply to each model
- When distributing models, users should not have to run through a dance of trying to recover what tools you applied

The scripts in `prepare/` establish a JSON-based pipeline.
Each step in the pipeline consumes a JSON object, adds a field, and passes the JSON object to the next step.
Importantly, each step also overwrites the `text` field of the JSON object, so that each step can easily access the output of the previous step.
(This avoids the need for each step to deduce what the previous step was).

Here is an example preprocessing pipeline.
(Assume this script is named `pre.sh`).
This scripts expects French input in the form of raw, untokenized sentences.
It applies [term masking](masking/), runs the Moses tokenizer, and applies BPE subword processing.
Note that BPE subword processing takes in a dictionary of masks that should not be split up, an important component of masking.
Each of these scripts and their models are assumed to be in the current directory.

```bash
#!/usr/bin/env bash

lang=${1:-fr}
rundir=$(dirname $0)
$rundir/sockeye_scripts/preparation/wrap_in_json -r raw_text | python $rundir/sockeye_scripts/masking/mask_terms.py --json --pattern-files /home/hltcoe/mpost/exp/robust19/patterns.txt --add-index | $rundir/sockeye_scripts/preparation/wrap_in_json text tok_text $rundir/tokenizer/moses_tokenizer | $rundir/sockeye_scripts/preparation/prepare.py --subword-type bpe --subword-model $rundir/subword.model --subword-glossary __EMAIL_1__ __EMOJI_1__ __EMOJI_2__ __HANDLE_1__ __HASHTAG_1__ __HASHTAG_10__ __HASHTAG_11__ __HASHTAG_2__ __HASHTAG_3__ __HASHTAG_4__ __HASHTAG_5__ __HASHTAG_6__ __HASHTAG_7__ __HASHTAG_8__ __HASHTAG_9__ __URL_1__ __URL_2__
```

JSON is enabled in two ways:

- scripts themselves can be JSON aware (able to read and write JSON)
- the `wrap_in_json` script can be used to wrap any command in JSON

The output of running this script is the following object:

```bash
$ echo "Je suis sur l'internet chez http://mjpost.github.io/" | ./bundle/pre.sh
{"raw_text": "Je suis sur l'internet chez http://mjpost.github.io/", "text": "Je suis sur l' internet chez __URL_1__", "masked_text": "Je suis sur l'internet chez __URL_1__", "masks": [{"maskstr": "__URL_1__", "matched": "http://mjpost.github.io/", "replacement": "http://mjpost.github.io/"}], "tok_text": "Je suis sur l' internet chez __URL_1__", "subword_text": "Je suis sur l' internet chez __URL_1__", "subword_method": "bpe"}
```

The JSON object is printed on a single line.
Here is the output formatted across multiple lines, for readability:

```json
{
  "raw_text": "Je suis sur l'internet chez http://mjpost.github.io/",
  "masked_text": "Je suis sur l'internet chez __URL_1__",
  "masks": [
    {
      "maskstr": "__URL_1__",
      "matched": "http://mjpost.github.io/",
      "replacement": "http://mjpost.github.io/"
    }
  ],
  "tok_text": "Je suis sur l' internet chez __URL_1__",
  "subword_text": "Je suis sur l' internet chez __URL_1__",
  "subword_method": "bpe"
  "text": "Je suis sur l' internet chez __URL_1__",
}
```

Note that `wrap_in_json` is used in two ways: at the beginning, with the `-r` flag, to turn raw text into JSON.
Note that it will also set the `text` field.
In this situation, it takes the name of a field, `raw_text`, and adds that to the JSON object.
Later, it is used to wrap scripts that are not JSON-aware.
In this situation, it requires three arguments: (1) the field to read, (2) the field to write, and (3) the command to call.
Usually, (2) is just `text`, which I have noted is always set by JSON aware scripts.

Also note the JSON object can contain other fields, such as the set of masks that were applied.
This can be useful in postprocessing, assuming that the decoder call passes the JSON object through.

## Model API

The bundled model is created in my [tape4nmt repo](https://github.com/mjpost/tape4nmt/).
It creates a bundle with all the model files and preprocessing scripts contained with it, and defines a command-line API via three scripts.

- `pre.sh`, which takes raw text or a JSON object and applies all preprocessing.
- `post.sh`, which takes the output of the decoder and produces human-readable text by applying detokenization and other related post-processing scripts.
- `translate.sh`, which takes raw input, calls `pre.sh`, passes it through the decoder, and passes that through `post.sh`.
- (Optional) `score.sh`, which takes input pairs and scores them
