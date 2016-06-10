#!/bin/sh

ROOT=`dirname $0`/..

. $ROOT/bin/common.sh

python -m cProfile -o $ROOT/scratch/profile.out $ROOT/pyrtree/bench/bench_rtree.py

$VENV/bin/runsnake $ROOT/scratch/profile.out