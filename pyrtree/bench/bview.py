#!/usr/bin/env python

# quick'n'dirty benchmark viewer.

import pylab as pl
import sys, csv


if (__name__ == "__main__"):


    file_counts = len(sys.argv) - 1
    

    def pos(row,col):
        rr= (row * file_counts) + col
        return rr + 1
    
    for (column_number, filename) in enumerate(sys.argv[1:]):
        data = {}

        vals = csv.reader(open(filename))
        
        for (fnum,key,v) in vals:
            d = data
            if key not in d: d[key] = ([],[])
            xs,ys = d[key]
            xs.append(int(fnum))
            ys.append(float(v))

        sz = pos(len(data.keys()) - 1,file_counts - 1)

        for i,k in enumerate(data.keys()):
            xs,ys = data[k]
            pl.subplot(len(data.keys()),file_counts,pos(i , column_number))
            pl.xlabel(filename)
            pl.plot(xs,ys, label=k)
            pl.legend()

    pl.ion()
    pl.show()
