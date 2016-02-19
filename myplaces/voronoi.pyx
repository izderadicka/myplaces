'''
Created on Sep 29, 2013
@author: ivan
'''

import sys
import numpy as np
cimport numpy as np

DTYPE=np.double
ctypedef np.double_t DTYPE_t
ITYPE=np.int
ctypedef np.int_t ITYPE_t

cdef bint check_outside(np.ndarray[DTYPE_t, ndim=1] point, np.ndarray[DTYPE_t, ndim=1] bbox):
    cdef  np.ndarray[DTYPE_t, ndim=1] rp
    rp=np.round(point, 4)
    return rp[0]<bbox[0] or rp[0]>bbox[2] or rp[1]< bbox[1] or rp[1]>bbox[3]

cdef void move_point(np.ndarray[DTYPE_t, ndim=1] start, np.ndarray[DTYPE_t, ndim=1] end, np.ndarray[DTYPE_t, ndim=1] bbox):
    cdef: 
        np.ndarray[DTYPE_t, ndim=1] vector=end-start
        double c
    c=calc_shift(start, vector, bbox)
    if c>0 and c<1:
        start[0:2]=start+c*vector
       
    
cdef double calc_shift(np.ndarray[DTYPE_t, ndim=1] point, np.ndarray[DTYPE_t, ndim=1] vector, np.ndarray[DTYPE_t, ndim=1] bbox):
    cdef: 
        double c = np.inf, m, a
        int l 
    for l in range(bbox.shape[0]):
        m=bbox[l]
        a=(m-point[l%2])/vector[l%2]
        if  a>0 and  not check_outside(point+a*vector, bbox):
            if abs(a)<abs(c):
                c=a
    return c 

from scipy.spatial import Voronoi   
def voronoi3(P, bbox_in=None): 
    P=np.asarray(P)
    if not bbox_in:
        xmin=P[:,0].min()
        xmax=P[:,0].max()
        ymin=P[:,1].min()
        ymax=P[:,1].max()
        xrange=(xmax-xmin) * 0.3333333
        yrange=(ymax-ymin) * 0.3333333
        bbox_in=(xmin-xrange, ymin-yrange, xmax+xrange, ymax+yrange)
    
    vor=Voronoi(P)
    cdef: 
        int i, istart, iend, N, ifirst, isecond, orientation
        double c
        np.ndarray[DTYPE_t, ndim=1] center,start, end, first, second, edge, vector, midpoint, bbox
        np.ndarray[DTYPE_t, ndim=2] vs, points   
        np.ndarray[ITYPE_t, ndim=2] rvs, rpoints
    bbox=np.round(np.asarray(bbox_in, DTYPE),4)    
    center = vor.points.mean(axis=0)
    vs=vor.vertices
    rvs=np.asarray(vor.ridge_vertices, dtype=ITYPE)
    rpoints=np.asarray(vor.ridge_points, dtype=ITYPE)
    N=rvs.shape[0]
    points=vor.points
    segments=[]
    
    for i in range(N):
        istart=rvs[i,0]
        iend=rvs[i,1]
        if istart<0 or iend<=0:
            start=vs[istart] if istart>=0 else vs[iend]
            if check_outside(start, bbox) :
                    continue
            ifirst = rpoints[i,0]
            isecond = rpoints[i,1]
            first = points[ifirst]
            second = points[isecond]
            edge= np.subtract(second, first)
            vector=np.array([-edge[1], edge[0]])
            midpoint= (second+first)/2
            orientation=np.sign(np.dot(midpoint-center, vector))
            vector=orientation*vector
            c=calc_shift(start, vector, bbox)
            segments.append([start,start+c*vector])
        else:
            start=np.copy(vs[istart])
            end= np.copy(vs[iend])
            if check_outside(start, bbox):
                move_point(start,end, bbox)
            if check_outside(end, bbox):
                move_point(end,start, bbox)
                
            segments.append( [start, end] )
        
        
    return segments



