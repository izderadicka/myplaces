'''
Created on Sep 29, 2013
@author: ivan

Inspired by code https://github.com/rougier/neural-networks/blob/master/voronoi.py from Nicolas P. Rougier
'''

import sys
import numpy as np
import matplotlib.tri
import matplotlib.pyplot as plt
import time
from fortune import computeVoronoiDiagram, Site

def circumcircle2(T):
    P1,P2,P3=T[:,0], T[:,1], T[:,2]
    delta_a = P2 - P1
    delta_b = P3 - P2
    aSlope = delta_a[:,1]/delta_a[:,0]
    bSlope = delta_b[:,1]/delta_b[:,0]
    center_x= (aSlope*bSlope*(P1[:,1] - P3[:,1]) + bSlope*(P1[:,0] + P2 [:,0]) - aSlope*(P2[:,0]+P3[:,0]) )/(2* (bSlope-aSlope))
    center_y = -1*(center_x - (P1[:,0]+P2[:,0])/2)/aSlope + (P1[:,1]+P2[:,1])/2;
    return np.array((center_x, center_y)).T

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
   

def voronoi2(P, bbox=None):
    if not isinstance(P, np.ndarray):
        P=np.array(P)
    if not bbox:
        xmin=P[:,0].min()
        xmax=P[:,0].max()
        ymin=P[:,1].min()
        ymax=P[:,1].max()
        xrange=(xmax-xmin) * 0.3333333
        yrange=(ymax-ymin) * 0.3333333
        bbox=(xmin-xrange, ymin-yrange, xmax+xrange, ymax+yrange)
    bbox=np.round(bbox,4)
        
    D = matplotlib.tri.Triangulation(P[:,0],P[:,1])
    T = D.triangles
    n = T.shape[0]
    C = circumcircle2(P[T])
    
    segments = []
    for i in range(n):
        for j in range(3):
            k = D.neighbors[i][j]
            if k != -1:
                #cut segment to part in bbox
                start,end=C[i], C[k]
                if check_outside(start, bbox):
                    start=move_point(start,end, bbox)
                    if  start is None:
                        continue
                if check_outside(end, bbox):
                    end=move_point(end,start, bbox)
                    if  end is None:
                        continue
                segments.append( [start, end] )
            else:
                #ignore center outside of bbox
                if check_outside(C[i], bbox) :
                    continue
                first, second, third=P[T[i,j]], P[T[i,(j+1)%3]], P[T[i,(j+2)%3]]
                edge=np.array([first, second])
                vector=np.array([[0,1], [-1,0]]).dot(edge[1]-edge[0])
                line=lambda p: (p[0]-first[0])*(second[1]-first[1])/(second[0]-first[0])  -p[1] + first[1]
                orientation=np.sign(line(third))*np.sign( line(first+vector))
                if orientation>0:
                    vector=-orientation*vector
                c=calc_shift(C[i], vector, bbox)
                if c is not None:    
                    segments.append([C[i],C[i]+c*vector])
    return segments

METHODS=['matplotlib',# calculated from Delaunay triagulation as dual graph
         'fortune', #Fortune's algorithm in pure python
         ]


if __name__=='__main__':
    method='matplotlib'
    if len(sys.argv)>1:
        method=sys.argv[1]
    if method not in METHODS:
        print >>sys.stderr, 'Invalid method %s'&method
        sys.exit(1)
#     x,y=np.mgrid[10:101:10, 10:101:10]
#     z=np.array([x,y])
    #points=np.loads(data)
    points=np.random.rand(10,2)*100  
    #z.T.reshape(100,2)#np.array([[10,10], [10, 20], [20,20], [20,10]])#
    #from myplaces.test_cases.pivovary_data import points
    #points=np.array(points)
    print repr(points)
    now=time.time()
    if method=='matplotlib':
        lines=voronoi2(points, (-20,-20, 120, 120))
    elif method=='fortune':
        sites=[Site(p[0], p[1], i) for i,p in enumerate(points)]
        vertices, _equations, edges= computeVoronoiDiagram(sites)
        lines=[(vertices[e[1]], vertices[e[2]]) for e in edges if e[1]!=-1 and e[2]!=-1]
    print 'voronoi took %f secs' % (time.time()-now, )
    #print lines
    plt.scatter(points[:,0], points[:,1], color="blue")
    tri=matplotlib.tri.Triangulation(points[:,0], points[:,1])
    plt.triplot(points[:,0], points[:,1], tri.triangles, color="yellow")
    circles=circumcircle2(points[tri.triangles])
    plt.scatter(circles[:,0], circles[:,1], 40, color='green', marker='x')
    for i,c in enumerate(circles):
        r=np.square(c-points[tri.triangles[i][0]])
        r=np.sqrt(r[0]+r[1])
        circle=plt.Circle(c, r, color='lightgrey', fill=False )
        plt.gca().add_artist(circle)
    lines = matplotlib.collections.LineCollection(lines, color='red')
    plt.gca().add_collection(lines)
    #plt.axis((10,20, 47,53))
    plt.axis((-20,120, -20,120))
    plt.show()


