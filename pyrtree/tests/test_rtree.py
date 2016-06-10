# FIXME: path hackery.
if __name__ == "__main__":
    import sys, os
    mypath = os.path.dirname(sys.argv[0])
    sys.path.append(os.path.abspath(os.path.join(mypath, "../../")))

from pyrtree import Rect, RTree
#from pyrtree.rect import *

import collections
import unittest as ut
import random, math
from testutil import *

def rr():
    return random.uniform(0.0,10.0)

class TstO(object): 
    """ Dummy test object to store in r-trees. """
    def __init__(self,r):
        self.rect = r
    def walk(self,pred):
        if pred(self): yield self

class RectangleGen(object):
    """ Generate random rectangles w/ various properties. """
    def rect(self, size=10.0):
        x,y,w,h = rr(),rr(),random.uniform(0.0,size), random.uniform(0.0,size)
        r = Rect(x,y,x+w,y+h)
        assert(not r.swapped_x)
        assert(not r.swapped_y)
        return r

    def intersectingWith(self,ra):
        rb_x = random.uniform(ra.x,ra.xx)
        rb_y = random.uniform(ra.y,ra.yy)
        return Rect(rb_x,rb_y,rb_x + rr(),rb_y + rr())

    def disjointWith(self, ra):
        ax,ay,aw,ah = ra.extent()
        w,h = rr(),rr()
        distsq = max(w*w + h*h, aw*aw + ah * ah)
        dist = 2.0 * math.sqrt(distsq) + random.uniform(0.1, 1.0)
        ang = random.uniform(0.0, 2.0 * math.pi)
        x = math.cos(ang) * dist
        y = math.sin(ang) * dist
        return Rect(ax+x,ay+y,ax+x+w,ay+y+h)

    def pointInside(self, r):
        return (random.uniform(r.x,r.xx),random.uniform(r.y,r.yy))

    def pointOutside(self,r):
        return self.pointInside(self.disjointWith(r))

    def rswap(self, a, b):
        rr = [a,b]
        random.shuffle(rr)
        return (rr[0],rr[1])

    def intersectingPair(self):
        ra = self.rect()
        rb = self.intersectingWith(ra)
        return self.rswap(ra,rb)

    def disjointPair(self):
        ra = self.rect()
        rb = self.disjointWith(ra)
        return self.rswap(ra,rb)


G = RectangleGen()

class RectangleTests(ut.TestCase):
    def testCons(self):
        r = Rect(0,0,10,10)
        self.assertTrue(r is not None)
        self.assertTrue(r is not NullRect)

    
    def testIntersection(self):
        ra = Rect(0,0,10,10)
        rb = Rect(5,5,15,15)
        res = ra.intersect(rb)
        x,y,w,h = res.extent()
        self.assertEquals(x,5)
        self.assertEquals(y,5)
        self.assertEquals(w,5)
        self.assertEquals(h,5)
        self.assertEquals(res.area(), 25)

        rc = Rect(0,0,10,10)
        rd = Rect(11,11,21,21)
        res2 = rc.intersect(rd)
        self.assertEquals(res2.area(),0)
        self.assertTrue(res2 is NullRect)

        for i in range(1000):
            a,b = G.intersectingPair()
            self.assertTrue(a.intersect(b).area() > 0.0)
            c,d = G.disjointPair()
            self.assertEquals(c.intersect(d).area(), 0)

        self.assertTrue(ra.intersect(NullRect) is NullRect)
        self.assertTrue(NullRect.intersect(ra) is NullRect)

    def testUnion(self):
        ra = Rect(0,0,10,10)
        rb = Rect(-10,-10,1,1)
        x,y,w,h = ra.union(rb).extent()
        self.assertEquals(x,-10)
        self.assertEquals(y,-10)
        self.assertEquals(w,20)
        self.assertEquals(h,20)

        for i in range(1000):
            a,b = G.rect(),G.rect()
            u = a.union(b)
            self.assertTrue(a.intersect(u).area() > 0)
            self.assertTrue(u.intersect(a).area() > 0)
            self.assertTrue(b.intersect(u).area() > 0)
            self.assertTrue(u.intersect(b).area() > 0)
            self.assertTrue(u.area() >= (max(a.area(),b.area())), 
                            "union area (iter %d) fail %f >= %f" % (i,u.area(),(max(a.area(),b.area()))))

            c,d = G.disjointPair()
            u2 = c.union(d)
            self.assertTrue(c.intersect(u2).area() > 0)
            self.assertTrue(u2.intersect(c).area() > 0)
            self.assertTrue(d.intersect(u2).area() > 0)
            self.assertTrue(u2.intersect(d).area() > 0)
            self.assertTrue(u2.area() > c.area())
            self.assertTrue(u2.area() > d.area())
            self.assertTrue(u2.area() >= (c.area() + d.area()))

    def testContainPoint(self):
        rs = take(100,G.rect)
        for r in rs:
            self.assertTrue(r.does_containpoint(G.pointInside(r)))
            self.assertFalse(r.does_containpoint(G.pointOutside(r)))

    def testContainRects(self):
        for r in take(1000,G.rect):
            self.assertTrue(r.does_contain(r))
            ix = r.intersect(G.intersectingWith(r))

            self.assertTrue(r.does_contain(ix))
            out = G.disjointWith(r)
            self.assertFalse(r.does_contain(out))
            
            

class RTreeTest(ut.TestCase):
    def testCons(self):
        n = RTree()

    def invariants(self, tree):
        self.assertEquals(tree.cursor.index, 0)
        self._invariants(tree.cursor, {})

    def _invariants(self,node, seen):
        idx = node.index

        self.assertTrue(idx not in seen)

        seen[idx] = True

        if node.holds_leaves():
            #print("node: %d, children: %r" % (node.index, [c.index for c in node.children()]))
            self.assertTrue(node.nchildren() == 0 or node.get_first_child().is_leaf())
            for c in node.children():
                #print(c.index)
                self.assertTrue(c.is_leaf())
                self.assertTrue(isinstance(c.leaf_obj(),TstO))
        else:
            for c in node.children():
                self.assertTrue(not c.is_leaf())
        self.assertEquals(idx,node.index)

        r = Rect(node.rect.x, node.rect.y, node.rect.xx, node.rect.yy)
        for c in node.children():
            assert r.does_contain(c.rect)

        self.assertEquals(idx,node.index)

        for c in node.children():
            if not c.is_leaf(): self._invariants(c, seen)

        self.assertEquals(idx,node.index)

    def testContainer(self):
        """ Test container-like behaviour. """
        xs = [ TstO(r) for r in take(100,G.rect, 0.1) ]
        tree = RTree()
        for x in xs: 
            tree.insert(x,x.rect)
            self.invariants(tree)

        ws = [ x.leaf_obj() for x in tree.walk(lambda x,y: True) if x.is_leaf() ]
        self.invariants(tree)
        rrs = collections.defaultdict(int)
        
        for w in ws:
            rrs[w] = rrs[w] + 1

        for x in xs: self.assertEquals(rrs[x], 1)

    def testDegenerateContainer(self):
        """ Tests that an r-tree still works like a container even with highly overlapping rects. """
        xs = [ TstO(r) for r in take(1000,G.rect, 20.0) ]
        tree = RTree()
        for x in xs: 
            tree.insert(x,x.rect)
            self.invariants(tree)

        ws = [ x.leaf_obj() for x in tree.walk(lambda x,y: True) if x.is_leaf() ]
        for x in xs: self.assertTrue(x in ws)


    def testInsertSame(self):
        tree = RTree()
        rect = G.rect()
        xs = [ TstO(rect) for i in range(11) ]
        for x in xs:
            tree.insert(x,x.rect)
            self.invariants(tree)


    def testPointQuery(self):
        xs = [ TstO(r) for r in take(1000,G.rect, 0.01) ]
        tree = RTree()
        for x in xs:
            tree.insert(x,x.rect)
            self.invariants(tree)
        
        for x in xs:
            qp = G.pointInside(x.rect)
            self.assertTrue(x.rect.does_containpoint(qp))
            op = G.pointOutside(x.rect)
            rs = list([r.leaf_obj() for r in tree.query_point(qp)])
            self.assertTrue(x in rs, "Not in results of len %d :(" % (len(rs)))
            rrs = list([r.leaf_obj() for r in tree.query_point(op)])
            self.assertFalse(x in rrs)

    def testRectQuery(self):
        xs = [ TstO(r) for r in take(1000, G.rect, 0.01) ]
        rt = RTree()
        for x in xs: 
            rt.insert(x,x.rect)
            self.invariants(rt)

        for x in xs:
            qrect = G.intersectingWith(x.rect)
            orect = G.disjointWith(x.rect)
            self.assertTrue(qrect.does_intersect(x.rect))
            p = G.pointInside(x.rect)
            res = list([ro.leaf_obj() for ro in rt.query_point(p)])
            self.invariants(rt)
            self.assertTrue(x in res)
            res2 = list([r.leaf_obj() for r in rt.query_rect(qrect)])
            self.assertTrue(x in res2)
            rres = list([r.leaf_obj() for r in rt.query_rect(orect)])
            self.assertFalse(x in rres)


if __name__ == '__main__':
    ut.main()
