#!/bin/sh

mkdir -p data

# timeout 30 ../code/build/OldSection12/OldSection12 $1 $1 > data/$1-old
# timeout 30 ../code/build/Section12/Section12 $1 $1 > data/$1-opt

./fps-visualise.py data/$1-opt data/$1-old ../report/figures/fps-$1-scene.pdf
