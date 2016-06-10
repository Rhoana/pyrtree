#!/bin/sh

# TODO: fix a bunch of hardcoding

# for now, I assume: virtualenv set up in scratch/libspatial_rtree -
# it has a non-buggy Rtree installed. (I used SVN; PyPi versions
# didn't work out.)
#  
# AND, a 1.5 or later version of libspatialindex was compiled
#  and installed (with prefix=) to scratch/libspatialindex/
#
# download and untar libspatialindex, then:
# 
# configure prefix=/path/to/scratch/libspatialindex ; make ; make install


# The menthod I used for rtree inst: 
# ./scratch/libspatial_rtree/bin/pip install -e svn+http://svn.gispython.org/svn/gispy/Rtree/trunk#egg=Rtree

ROOT=`dirname $0`/..
. $ROOT/bin/common.sh


SIDX=$ROOT/scratch/libspatialindex/lib

LD_LIBRARY_PATH=$SIDX
export LD_LIBRARY_PATH

$PYTHON $ROOT/pyrtree/bench/bench_libspatial.py