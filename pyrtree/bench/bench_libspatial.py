# Like bench_rtree but uses the libspatialindex c library. For comparison!
# http://pypi.python.org/pypi/Rtree

# TODO: path hackery.
if __name__ == "__main__":
    import sys, os
    mypath = os.path.dirname(sys.argv[0])
    sys.path.append(os.path.abspath(os.path.join(mypath, "../../")))

from pyrtree.bench.bench_rtree import ITER,INTERVAL
from pyrtree.tests.test_rtree import RectangleGen,TstO
import time
from rtree import Rtree

if __name__ == "__main__":
    G = RectangleGen()
    idx = Rtree() # this is a libspatialindex one.
    start = time.clock()
    interval_start = time.clock()
    for v in range(ITER):
        if 0 == (v % INTERVAL):
            # interval time taken, total time taken, # rects, cur max depth
            t = time.clock()
            
            dt = t - interval_start
            print("%d,%s,%f" % (v, "itime_t", dt))
            print("%d,%s,%f" % (v, "avg_insert_t", (dt/float(INTERVAL))))
            #print("%d,%s,%d" % (v, "max_depth", rt.node.max_depth()))
            #print("%d,%s,%d" % (v, "mean_depth", rt.node.mean_depth()))

            interval_start = time.clock()
        rect = G.rect(0.000001)
        idx.add(v,rect.coords())

