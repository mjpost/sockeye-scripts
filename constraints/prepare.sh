#!/bin/bash

# This script will generate the random constraint sets from a WMT test set and language pair.

SOURCE=en
TARGET=de
PAIR=$SOURCE-$TARGET

WMT=${1:-wmt17}
BPE_MODEL=${2:-bpe.model}

if [[ ! -e $BPE_MODEL ]]; then
    echo "Can't find BPE model '$BPE_MODEL'"
    exit 1
fi

scriptdir=$(dirname $0)

sacrebleu -t $WMT -l $PAIR --echo both | unpaste $WMT.{$SOURCE,$TARGET}

for ext in $SOURCE $TARGET; do
    cat $WMT.$ext| scarlett_tokenizer $ext | tee $WMT.tok.$ext | apply_bpe.py -c ${BPE_MODEL} > $WMT.bpe.$ext
done

# Create the baseline source file
paste $WMT.tok.{$SOURCE,$TARGET} | ${scriptdir}/jsonify.py --bpe ${BPE_MODEL} > $WMT.json

# Use the entire reference as a phrasal constraint
paste $WMT.tok.{$SOURCE,$TARGET} | ${scriptdir}/scripts/jsonify.py --bpe ${BPE_MODEL} -a > $WMT.ref.json

# Grab random one-word phrases
for n in 1 2 3 4; do
    paste $WMT.tok.{$SOURCE,$TARGET} | ${scriptdir}/scripts/jsonify.py --bpe ${BPE_MODEL} -r $n -p 1 > $WMT.constrained.rand${n}.json
done

# Grab random length-n phrases
for p in 2 3 4; do
    paste $WMT.tok.{$SOURCE,$TARGET} | ${scriptdir}/scripts/jsonify.py --bpe ${BPE_MODEL} -r 1 -p 2 > $WMT.constrained.phr${p}.json
done
