#!/bin/bash

# Takes a corpus and scores all of its lines using dual cross-entropy filtering.
#
# Inputs:
# - the corpus (two sides)
# - a SRC-TRG scoring model
# - a TRG-SRC scoring model
#
# Outputs:
# - scores, parallel to the input

#$ -S /bin/bash -V
#$ -cwd
#$ -q gpu.q@@1080 -l gpu=1,h_rt=1:00:00
#$ -j y -o logs
#$ -t 5002:6000 -tc 15

set -eu

TMPDIR=/expscratch/mpost

source=${1:-}
target=${2:-}
model1=${3:-}
model2=${4:-}
output=${5:-}

if [[ -z $output ]]; then
    echo "Usage: filter.sh corpus.src corpus.trg model.src-trg model.trg-src"
    exit 1
fi

# Make sure we have scoring models
if [[ ! -x $model1/score.sh || ! -x $model2/score.sh ]]; then
    echo "$model1 or $model2 doesn't look like a scoring model."
    exit 2
fi

# Make sure we can write to output
echo test > $output

tempdir=$(mktemp -d -p $TMPDIR)

split --numeric-suffixes=1 -a5 -l1000000 $source $tempdir/corpus.src. &
split --numeric-suffixes=1 -a5 -l1000000 $target $tempdir/corpus.trg. &
wait

numpieces=$(ls $tempdir/corpus.src.* | wc -l)
echo "Created $numpieces pieces"
ls $tempdir

# Run all the scoring pieces
qsub -sync y -l h_rt=2:00:00 -t 1:${numpieces} ~/code/sockeye-scripts/filtering/score.sh $tempdir/corpus.{src,trg} $model1 $tempdir/corpus.score.src-trg
qsub -sync y -l h_rt=2:00:00 -t 1:${numpieces} ~/code/sockeye-scripts/filtering/score.sh $tempdir/corpus.{trg,src} $model1 $tempdir/corpus.score.trg-src

# Merge
paste <(cat $tempdir/corpus.score.src-trg*) <(cat $tempdir/corpus.score.trg-src*) | ~/code/sockeye-scripts/filtering/combine_scores.py > $output

# cleanup
echo "Done. Run 'rm -rf $tempdir' to cleanup"
#rm -rf $tempdir
