import gc
# TODO: path hackery.
if __name__ == "__main__":
    import sys, os
    mypath = os.path.dirname(sys.argv[0])
    sys.path.append(os.path.abspath(os.path.join(mypath, "../../")))

from pyrtree.rtree import RTree
from pyrtree.tests.test_rtree import RectangleGen,TstO

import time

# TODO: make these command-line params.
import os

ITER=1000000 # one meeelion
if "TEST_ITER" in os.environ:
    ITER=int(os.getenv("TEST_ITER"))
INTERVAL=1000 # log at every 1k
if "TEST_INTERVAL" in os.environ:
    INTERVAL=int(os.getenv("TEST_INTERVAL"))


if __name__ == "__main__":
    gc.disable() # FFFFUUUUUUUUUUU
    G = RectangleGen()
    rt = RTree()
    start = time.clock()
    interval_start = time.clock()
    for v in range(ITER):
        if 0 == (v % INTERVAL):
            # interval time taken, total time taken, # rects, cur max depth
            t = time.clock()
            
            dt = t - interval_start
            print("%d,%s,%f" % (v, "itime_t", dt))
            print("%d,%s,%f" % (v, "avg_insert_t", (dt/float(INTERVAL))))
            for (k,val) in rt.stats.iteritems():
                print("%d,%s,%f" % (v, k, val))
            for k in rt.stats.keys():
                if k.endswith("_f"): rt.stats[k] = 0.0


            #print("%d,%s,%d" % (v, "max_depth", rt.node.max_depth()))
            #print("%d,%s,%d" % (v, "mean_depth", rt.node.mean_depth()))

            interval_start = time.clock()
        o = TstO(G.rect(0.000001))
        rt.insert(v,o.rect)

    # Done.

