'''
Created on Sep 29, 2013
@author: ivan
'''

import sys
import numpy as np

def check_outside(point, bbox):
    point=np.round(point, 4)
    return point[0]<bbox[0] or point[0]>bbox[2] or point[1]< bbox[1] or point[1]>bbox[3]

def move_point(start, end, bbox):
    vector=end-start
    c=calc_shift(start, vector, bbox)
    if c>0 and c<1:
        start=start+c*vector
        return start
    
def calc_shift(point, vector, bbox):
    c=sys.float_info.max
    for l,m in enumerate(bbox):
        a=(float(m)-point[l%2])/vector[l%2]
        if  a>0 and  not check_outside(point+a*vector, bbox):
            if abs(a)<abs(c):
                c=a
    return c if c<sys.float_info.max else None

from scipy.spatial import Voronoi   
def voronoi3(P, bbox=None): 
    P=np.asarray(P)
    if not bbox:
        xmin=P[:,0].min()
        xmax=P[:,0].max()
        ymin=P[:,1].min()
        ymax=P[:,1].max()
        xrange=(xmax-xmin) * 0.3333333
        yrange=(ymax-ymin) * 0.3333333
        bbox=(xmin-xrange, ymin-yrange, xmax+xrange, ymax+yrange)
    bbox=np.round(bbox,4)
    vor=Voronoi(P)
    center = vor.points.mean(axis=0)
    vs=vor.vertices
    segments=[]
    for i,(istart,iend) in enumerate(vor.ridge_vertices):
        if istart<0 or iend<=0:
            start=vs[istart] if istart>=0 else vs[iend]
            if check_outside(start, bbox) :
                    continue
            first,second = vor.ridge_points[i]
            first,second = vor.points[first], vor.points[second]
            edge= second - first
            vector=np.array([-edge[1], edge[0]])
            midpoint= (second+first)/2
            orientation=np.sign(np.dot(midpoint-center, vector))
            vector=orientation*vector
            c=calc_shift(start, vector, bbox)
            if c is not None:    
                segments.append([start,start+c*vector])
        else:
            start,end=vs[istart], vs[iend]
            if check_outside(start, bbox):
                start=move_point(start,end, bbox)
                if  start is None:
                    continue
            if check_outside(end, bbox):
                end=move_point(end,start, bbox)
                if  end is None:
                    continue
            segments.append( [start, end] )
        
        
    return segments



