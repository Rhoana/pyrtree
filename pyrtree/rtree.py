## R-tree.
# see doc/ref/r-tree-clustering-split-algo.pdf
from __future__ import absolute_import

MAXCHILDREN=10
MAX_KMEANS=5
import math, random, sys
import time
import array

from .rect import Rect, union_all, NullRect

class RTree(object):
    def __init__(self):
        self.count = 0
        self.stats = { 
            "overflow_f" : 0,
            "avg_overflow_t_f" : 0.0,
            "longest_overflow" : 0.0,
            "longest_kmeans" : 0.0,
            "sum_kmeans_iter_f" : 0,
            "count_kmeans_iter_f" : 0,
            "avg_kmeans_iter_f" : 0.0
            }

        # This round: not using objects directly -- they
        #   take up too much memory, and efficiency goes down the toilet
        #   (obviously) if things start to page.
        #  Less obviously: using object graph directly leads to really long GC
        #   pause times, too.
        # Instead, it uses pools of arrays:
        self.count = 0
        self.leaf_count = 0
        self.rect_pool = array.array('d')
        self.node_pool = array.array('L')
        self.leaf_pool = [] # leaf objects. 

        self.cursor = _NodeCursor.create(self, NullRect)

    def _ensure_pool(self, idx):
        if len(self.rect_pool) < (4*idx):
            self.rect_pool.extend([0,0,0,0] * idx)
            self.node_pool.extend([0,0] * idx)

    def insert(self,o, orect):
        self.cursor.insert(o,orect)
        assert(self.cursor.index == 0)

    def query_rect(self, r):
        for x in self.cursor.query_rect(r): yield x
    def query_point(self, p):
        for x in self.cursor.query_point(p): yield x
    def walk(self,pred):
        return self.cursor.walk(pred)

class _NodeCursor(object):
    @classmethod
    def create(cls, rooto, rect):
        idx = rooto.count
        rooto.count += 1
        
        rooto._ensure_pool(idx + 1)
        #rooto.node_pool.extend([0,0])
        #rooto.rect_pool.extend([0,0,0,0])

        retv = _NodeCursor(rooto,idx,rect,0,0)

        retv._save_back()
        return retv

    @classmethod
    def create_with_children(cls, children, rooto):
        rect = union_all([c for c in children])
        nr = Rect(rect.x,rect.y,rect.xx,rect.yy)
        assert(not rect.swapped_x)
        nc = _NodeCursor.create(rooto,rect)
        nc._set_children(children)
        assert(not nc.is_leaf())
        return nc

    @classmethod
    def create_leaf(cls, rooto, leaf_obj, leaf_rect):
        rect = Rect(leaf_rect.x,leaf_rect.y,leaf_rect.xx,leaf_rect.yy)
        rect.swapped_x = True # Mark as leaf by setting the xswap flag.
        res = _NodeCursor.create(rooto, rect)
        idx = res.index
        res.first_child = rooto.leaf_count
        rooto.leaf_count += 1
        res.next_sibling = 0
        rooto.leaf_pool.append(leaf_obj)
        res._save_back()
        res._become(idx)
        assert(res.is_leaf())
        return res

    __slots__ = ("root","npool","rpool","index","rect","next_sibling","first_child")

    def __init__(self, rooto, index, rect, first_child, next_sibling):
        self.root = rooto
        self.rpool = rooto.rect_pool
        self.npool = rooto.node_pool

        self.index = index
        self.rect = rect
        self.next_sibling = next_sibling
        self.first_child = first_child

    def walk(self, predicate):
        if (predicate(self, self.leaf_obj())):
            yield self
            if not self.is_leaf():
                for c in self.children():
                    for cr in c.walk(predicate):
                        yield cr

    def query_rect(self, r):
        """ Return things that intersect with 'r'. """
        def p(o,x): return r.does_intersect(o.rect)
        for rr in self.walk(p):
            yield rr

    def query_point(self,point):
        """ Query by a point """
        def p(o,x): return o.rect.does_containpoint(point)
            
        for rr in self.walk(p):
            yield rr

    def lift(self):
        return _NodeCursor(self.root,
                           self.index,
                           self.rect, 
                           self.first_child,
                           self.next_sibling)

    def _become(self, index):
        recti = index * 4
        nodei = index * 2
        rp = self.rpool
        x = rp[recti]
        y = rp[recti+1]
        xx = rp[recti+2]
        yy = rp[recti+3]

        if (x == 0.0 and y == 0.0 and xx == 0.0 and yy == 0.0): 
            self.rect = NullRect
        else:
            self.rect = Rect(x,y,xx,yy)

        self.next_sibling = self.npool[nodei]
        self.first_child = self.npool[nodei + 1]
        self.index = index

    def is_leaf(self):
        return self.rect.swapped_x

    def has_children(self):
        return not self.is_leaf() and 0 != self.first_child

    def holds_leaves(self):
        if 0 == self.first_child: return True
        else:
            return self.has_children() and self.get_first_child().is_leaf()
    
    def get_first_child(self):
        fc = self.first_child
        c = _NodeCursor(self.root,0,NullRect,0,0)
        c._become(self.first_child)
        return c

    def leaf_obj(self):
        if self.is_leaf(): return self.root.leaf_pool[self.first_child]
        else: return None

    def _save_back(self):
        rp = self.rpool
        recti = self.index * 4
        nodei = self.index * 2

        if self.rect is not NullRect:
            self.rect.write_raw_coords(rp, recti)
        else: 
            rp[recti] = 0
            rp[recti+1] = 0
            rp[recti+2] = 0
            rp[recti+3] = 0

        self.npool[nodei] = self.next_sibling
        self.npool[nodei + 1] = self.first_child
    
    def nchildren(self):
        i = self.index
        c = 0
        for x in self.children(): c += 1
        return c

    def insert(self, leafo, leafrect):
        index = self.index

        # tail recursion, made into loop:
        while True:
            if self.holds_leaves():
                self.rect = self.rect.union(leafrect)
                self._insert_child(_NodeCursor.create_leaf(self.root,leafo,leafrect))

                self._balance()
                
                # done: become the original again
                self._become(index)
                return
            else:
                # Not holding leaves, move down a level in the tree:

                # Micro-optimization: 
                #  inlining union() calls -- logic is:
                # ignored,child = min([ ((c.rect.union(leafrect)).area() - c.rect.area(),c.index) for c in self.children() ])
                child = None
                minarea = -1.0
                for c in self.children():
                    x,y,xx,yy = c.rect.coords()
                    lx,ly,lxx,lyy = leafrect.coords()
                    nx = x if x < lx else lx
                    nxx = xx if xx > lxx else lxx
                    ny = y if y < ly else ly
                    nyy = yy if yy > lyy else lyy
                    a = (nxx - nx) * (nyy - ny)
                    if minarea < 0 or a < minarea:
                        minarea = a
                        child = c.index
                # End micro-optimization

                self.rect = self.rect.union(leafrect)
                self._save_back()
                self._become(child) # recurse.
            
    def _balance(self):
        if (self.nchildren() <= MAXCHILDREN):
            return


        t = time.clock()
        
        cur_score = -10

        s_children = [ c.lift() for c in self.children() ]

        memo = {}

        clusterings = [ k_means_cluster(self.root,k,s_children) for k in range(2,MAX_KMEANS) ]
        score,bestcluster = max( [ (silhouette_coeff(c,memo),c) for c in clusterings ], key=lambda x:x[0])

        nodes = [ _NodeCursor.create_with_children(c,self.root) for c in bestcluster if len(c) > 0]

        self._set_children(nodes)
        
        dur = (time.clock() - t)
        c = float(self.root.stats["overflow_f"]) 
        oa = self.root.stats["avg_overflow_t_f"]
        self.root.stats["avg_overflow_t_f"] = (dur / (c + 1.0)) + (c * oa / (c + 1.0))
        self.root.stats["overflow_f"] += 1
        self.root.stats["longest_overflow"] = max(self.root.stats["longest_overflow"], dur)
            
    def _set_children(self, cs):
        self.first_child = 0

        if 0 == len(cs): 
            return

        pred = None
        for c in cs:
            if pred is not None: 
                pred.next_sibling = c.index
                pred._save_back()
            if 0 == self.first_child:
                self.first_child = c.index
            pred = c
        pred.next_sibling = 0
        pred._save_back()
        self._save_back()

    def _insert_child(self, c):
        c.next_sibling = self.first_child
        self.first_child = c.index
        c._save_back()
        self._save_back()
        

    def children(self):
        if (0 == self.first_child): return

        idx = self.index
        fc = self.first_child
        ns = self.next_sibling
        r = self.rect

        self._become(self.first_child)
        while True:
            yield self
            if 0 == self.next_sibling:
                break
            else: self._become(self.next_sibling)

        # Go back to becoming the same node we were.
        #self._become(idx)
        self.index = idx
        self.first_child = fc
        self.next_sibling = ns
        self.rect = r

def avg_diagonals(node, onodes, memo_tab):
    nidx = node.index
    sv = 0.0
    diag = 0.0
    for onode in onodes:
        k1 = (nidx,onode.index)
        k2 = (onode.index,nidx)
        if k1 in memo_tab: 
            diag = memo_tab[k1]
        elif k2 in memo_tab:
            diag = memo_tab[k2]
        else:
            diag = node.rect.union(onode.rect).diagonal()
            memo_tab[k1] = diag
        
        sv += diag

    return sv / len(onodes)

def silhouette_w(node, cluster, next_closest_cluster, memo):
    ndist = avg_diagonals(node, cluster, memo)
    sdist = avg_diagonals(node, next_closest_cluster, memo)
    return (sdist - ndist) / max(sdist,ndist)

def silhouette_coeff(clustering, memo_tab):
    # special case for a clustering of 1.0
    if (len(clustering) == 1): return 1.0

    coeffs = []
    for cluster in clustering:
        others = [ c for c in clustering if c is not cluster ]
        others_cntr = [ center_of_gravity(c) for c in others ]
        ws = [ silhouette_w(node,cluster,others[closest(others_cntr,node)], memo_tab) for node in cluster ]
        cluster_coeff = sum(ws) / len(ws)
        coeffs.append(cluster_coeff)
    return sum(coeffs) / len(coeffs)

def center_of_gravity(nodes):
    totarea = 0.0
    xs,ys = 0,0
    for n in nodes:
        if n.rect is not NullRect:
            x,y,w,h = n.rect.extent()
            a = w*h
            xs = xs + (a * (x + (0.5 * w)))
            ys = ys + (a * (y + (0.5 * h)))
            totarea = totarea + a
    return (xs / totarea), (ys / totarea)

def closest(centroids, node):
    x,y = center_of_gravity([node])
    dist = -1
    ridx = -1

    for (i,(xx,yy)) in enumerate(centroids):
        dsq = ((xx-x) ** 2) + ((yy-y) ** 2)
        if -1 == dist or dsq < dist:
            dist = dsq
            ridx = i
    return ridx


def k_means_cluster(root, k, nodes):
    t = time.clock()
    if len(nodes) <= k: return [ [n] for n in nodes ]
    
    ns = list(nodes)
    root.stats["count_kmeans_iter_f"] += 1

    # Initialize: take n random nodes.
    random.shuffle(ns)

    cluster_starts = ns[:k]
    cluster_centers = [ center_of_gravity([n]) for n in ns[:k] ]
    
    
    # Loop until stable:
    while True:
        root.stats["sum_kmeans_iter_f"] += 1
        clusters = [ [] for c in cluster_centers ]
        
        for n in ns: 
            idx = closest(cluster_centers, n)
            clusters[idx].append(n)
        
        #FIXME HACK TODO: is it okay for there to be empty clusters?
        clusters = [ c for c in clusters if len(c) > 0 ]

        for c in clusters:
            if (len(c) == 0):
                print("Errorrr....")
                print("Nodes: %d, centers: %s" % (len(ns),
                                                              repr(cluster_centers)))

            assert(len(c) > 0)
            
        rest = ns
        first = False

        new_cluster_centers = [ center_of_gravity(c) for c in clusters ]
        if new_cluster_centers == cluster_centers : 
            root.stats["avg_kmeans_iter_f"] = float(root.stats["sum_kmeans_iter_f"] / root.stats["count_kmeans_iter_f"])
            root.stats["longest_kmeans"] = max(root.stats["longest_kmeans"], (time.clock() - t))
            return clusters
        else: cluster_centers = new_cluster_centers
        
    
    
